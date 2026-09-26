from app.integrations.github.constants import PR_BRANCH, WORKFLOW_PATH
from tests.conftest import API, register, send_webhook
from tests.fakes import SAMPLE_BOM
from tests.test_github_connection import connect

RUN = {
    "id": 5001, "path": WORKFLOW_PATH, "event": "push", "head_sha": "a" * 40,
    "html_url": "https://github.com/octo/app/actions/runs/5001",
    "run_started_at": "2026-09-26T10:01:00Z", "updated_at": "2026-09-26T10:02:00Z", "conclusion": None,
}


def status_of(client, auth, repo_id=11):
    return client.get(f"{API}/repos/{repo_id}", headers=auth).json()["status"]


def test_repos_require_connection(client, auth):
    assert client.get(f"{API}/repos", headers=auth).status_code == 409


def test_full_scan_lifecycle(client, auth, github):
    connect(client, auth)
    repos = client.get(f"{API}/repos", headers=auth).json()
    assert [r["name"] for r in repos] == ["web", "app", "ops"]
    assert {r["status"] for r in repos} == {"not_enabled"}

    res = client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth)
    assert res.json() == {"opened": 1, "already_configured": 0, "errors": []}
    assert client.get(f"{API}/usage", headers=auth).json() == {"plan": "trial", "repo_limit": 2, "repos_enabled": 1}
    detail = client.get(f"{API}/repos/11", headers=auth).json()
    assert detail["status"] == "pr_open" and detail["pr"]["number"] == 7

    send_webhook(client, "pull_request", {
        "action": "closed", "repository": {"id": 11},
        "pull_request": {"merged": True, "merged_at": "2026-09-26T10:00:00Z", "head": {"ref": PR_BRANCH}},
    })
    assert status_of(client, auth) == "pending"

    send_webhook(client, "workflow_run", {"action": "requested", "repository": {"id": 11}, "workflow_run": RUN})
    assert status_of(client, auth) == "scanning"

    send_webhook(client, "workflow_run", {"action": "completed", "repository": {"id": 11}, "workflow_run": {**RUN, "conclusion": "success"}})
    detail = client.get(f"{API}/repos/11", headers=auth).json()
    assert detail["status"] == "scanned"
    assert detail["counts"] == {"libraries": 1, "models": 1, "services": 1}
    assert detail["scans"][0]["id"] == "5001" and detail["scans"][0]["commit_sha"] == "a" * 40
    assert client.get(f"{API}/repos/11/bom", headers=auth).json() == SAMPLE_BOM
    assert client.get(f"{API}/repos/11/scans/5001/bom", headers=auth).json() == SAMPLE_BOM

    assert client.post(f"{API}/repos/11/scans", headers=auth).status_code == 202
    assert ("dispatch", "octo/app") in github.calls
    assert status_of(client, auth) == "scanning"
    assert client.post(f"{API}/repos/11/scans", headers=auth).status_code == 409

    send_webhook(client, "workflow_run", {"action": "completed", "repository": {"id": 11}, "workflow_run": {**RUN, "id": 5002, "conclusion": "failure"}})
    detail = client.get(f"{API}/repos/11", headers=auth).json()
    assert detail["scans"][0]["status"] == "failure"
    assert detail["status"] == "scanned"

    assert client.delete(f"{API}/repos/11/enable", headers=auth).status_code == 204
    assert client.get(f"{API}/usage", headers=auth).json()["repos_enabled"] == 0


def test_trial_limit(client, auth):
    connect(client, auth)
    res = client.post(f"{API}/repos/enable", json={"repo_ids": [11, 12, 13]}, headers=auth)
    assert res.status_code == 402


def test_existing_workflow_skips_pr(client, auth, github):
    connect(client, auth)
    github.repos_with_workflow.add("octo/app")
    res = client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth).json()
    assert res == {"opened": 0, "already_configured": 1, "errors": []}
    assert status_of(client, auth) == "pending"


def test_pr_failure_is_reported(client, auth, github):
    connect(client, auth)
    github.failing_repos.add("octo/app")
    res = client.post(f"{API}/repos/enable", json={"repo_ids": [11, 12]}, headers=auth).json()
    assert res["opened"] == 1 and len(res["errors"]) == 1
    assert client.get(f"{API}/usage", headers=auth).json()["repos_enabled"] == 1


def test_invalid_bom_marks_scan_failed(client, auth, github):
    connect(client, auth)
    client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth)
    github.bom = {"not": "a bom"}
    send_webhook(client, "workflow_run", {"action": "completed", "repository": {"id": 11}, "workflow_run": {**RUN, "conclusion": "success"}})
    detail = client.get(f"{API}/repos/11", headers=auth).json()
    assert detail["status"] == "failed"
    assert "CycloneDX" in detail["scans"][0]["error"]


def test_users_cannot_see_each_others_repos(client, auth):
    connect(client, auth)
    client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth)
    other = register(client, "other@example.com")
    assert client.get(f"{API}/repos/11", headers=other).status_code == 404
    assert client.get(f"{API}/repos/11/bom", headers=other).status_code == 404
    assert client.delete(f"{API}/repos/11/enable", headers=other).status_code == 404


def test_webhook_signature_required(client):
    assert send_webhook(client, "ping", {}, secret="wrong").status_code == 401
    assert client.post(f"{API}/webhooks/github", json={}, headers={"X-GitHub-Event": "ping"}).status_code == 401
    assert send_webhook(client, "ping", {}).status_code == 202


def test_uninstall_webhook_removes_data(client, auth):
    connect(client, auth)
    client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth)
    send_webhook(client, "installation", {"action": "deleted", "installation": {"id": 999}})
    assert client.get(f"{API}/github/installation", headers=auth).json() is None
    assert client.get(f"{API}/usage", headers=auth).json()["repos_enabled"] == 0


def test_removed_repository_webhook(client, auth):
    connect(client, auth)
    client.post(f"{API}/repos/enable", json={"repo_ids": [11]}, headers=auth)
    send_webhook(client, "installation_repositories", {"action": "removed", "repositories_removed": [{"id": 11}]})
    assert client.get(f"{API}/repos/11", headers=auth).status_code == 404
