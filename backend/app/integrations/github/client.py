import base64
import io
import json
import logging
import threading
import time
import zipfile
from typing import Any

import httpx
import jwt

from app.core.config import Settings
from app.integrations.github import workflow
from app.integrations.github.constants import ARTIFACT_NAME, BOM_FILENAME, PR_BRANCH, WORKFLOW_FILE, WORKFLOW_PATH

log = logging.getLogger(__name__)

_HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "bomwatcher"}


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code


def _raise_for_status(res: httpx.Response) -> None:
    if res.is_success:
        return
    try:
        message = res.json().get("message", res.text)
    except ValueError:
        message = res.text
    raise GitHubAPIError(res.status_code, f"GitHub API {res.status_code}: {message}")


class GitHubApp:
    def __init__(self, settings: Settings, http: httpx.Client | None = None):
        self._settings = settings
        self._http = http or httpx.Client(base_url=settings.github_api_url, headers=_HEADERS, timeout=30)
        self._tokens: dict[int, tuple[str, float]] = {}
        self._lock = threading.Lock()

    @property
    def configured(self) -> bool:
        return self._settings.github_app_configured

    def install_url(self, state: str) -> str:
        return f"https://github.com/apps/{self._settings.github_app_slug}/installations/new?state={state}"

    def _app_jwt(self) -> str:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self._settings.github_app_id}
        return jwt.encode(payload, self._settings.github_private_key_pem, algorithm="RS256")

    def _app_request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        res = self._http.request(method, path, headers={"Authorization": f"Bearer {self._app_jwt()}"}, **kwargs)
        _raise_for_status(res)
        return res

    def get_installation(self, installation_id: int) -> dict[str, Any]:
        return self._app_request("GET", f"/app/installations/{installation_id}").json()

    def delete_installation(self, installation_id: int) -> None:
        self._app_request("DELETE", f"/app/installations/{installation_id}")

    def installation_token(self, installation_id: int) -> str:
        with self._lock:
            cached = self._tokens.get(installation_id)
            if cached and cached[1] > time.time() + 60:
                return cached[0]
        data = self._app_request("POST", f"/app/installations/{installation_id}/access_tokens").json()
        with self._lock:
            self._tokens[installation_id] = (data["token"], time.time() + 55 * 60)
        return data["token"]

    def for_installation(self, installation_id: int) -> "InstallationClient":
        return InstallationClient(self, installation_id)

    def request_as_installation(self, installation_id: int, method: str, path: str, **kwargs: Any) -> httpx.Response:
        token = self.installation_token(installation_id)
        res = self._http.request(method, path, headers={"Authorization": f"token {token}"}, follow_redirects=True, **kwargs)
        _raise_for_status(res)
        return res


class InstallationClient:
    def __init__(self, app: GitHubApp, installation_id: int):
        self._app = app
        self._installation_id = installation_id
        self._settings = app._settings

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        return self._app.request_as_installation(self._installation_id, method, path, **kwargs)

    def list_repositories(self) -> list[dict[str, Any]]:
        repos: list[dict[str, Any]] = []
        page = 1
        while True:
            data = self._request("GET", "/installation/repositories", params={"per_page": 100, "page": page}).json()
            repos.extend(data["repositories"])
            if len(repos) >= data["total_count"] or not data["repositories"]:
                return repos
            page += 1

    def workflow_exists(self, full_name: str, ref: str) -> bool:
        try:
            self._request("GET", f"/repos/{full_name}/contents/{WORKFLOW_PATH}", params={"ref": ref})
            return True
        except GitHubAPIError as e:
            if e.status_code == 404:
                return False
            raise

    def open_workflow_pull_request(self, full_name: str, default_branch: str) -> dict[str, Any]:
        owner = full_name.split("/", 1)[0]
        existing = self._request("GET", f"/repos/{full_name}/pulls", params={"head": f"{owner}:{PR_BRANCH}", "state": "open"}).json()
        if existing:
            return existing[0]

        base_sha = self._request("GET", f"/repos/{full_name}/git/ref/heads/{default_branch}").json()["object"]["sha"]
        try:
            self._request("POST", f"/repos/{full_name}/git/refs", json={"ref": f"refs/heads/{PR_BRANCH}", "sha": base_sha})
        except GitHubAPIError as e:
            if e.status_code != 422:
                raise
            self._request("PATCH", f"/repos/{full_name}/git/refs/heads/{PR_BRANCH}", json={"sha": base_sha, "force": True})

        content = workflow.render_workflow(default_branch, self._settings.scan_action_ref)
        body: dict[str, Any] = {
            "message": workflow.COMMIT_MESSAGE,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": PR_BRANCH,
        }
        try:
            current = self._request("GET", f"/repos/{full_name}/contents/{WORKFLOW_PATH}", params={"ref": PR_BRANCH}).json()
            body["sha"] = current["sha"]
        except GitHubAPIError as e:
            if e.status_code != 404:
                raise
        self._request("PUT", f"/repos/{full_name}/contents/{WORKFLOW_PATH}", json=body)

        return self._request("POST", f"/repos/{full_name}/pulls", json={
            "title": workflow.PR_TITLE,
            "head": PR_BRANCH,
            "base": default_branch,
            "body": workflow.PR_BODY,
        }).json()

    def dispatch_scan(self, full_name: str, ref: str) -> None:
        self._request("POST", f"/repos/{full_name}/actions/workflows/{WORKFLOW_FILE}/dispatches", json={"ref": ref})

    def download_bom(self, full_name: str, run_id: int) -> dict[str, Any]:
        limit = self._settings.max_artifact_bytes
        artifacts = self._request("GET", f"/repos/{full_name}/actions/runs/{run_id}/artifacts").json()["artifacts"]
        artifact = next((a for a in artifacts if a["name"] == ARTIFACT_NAME and not a.get("expired")), None)
        if artifact is None:
            raise GitHubAPIError(404, f"Run {run_id} has no '{ARTIFACT_NAME}' artifact")
        if artifact.get("size_in_bytes", 0) > limit:
            raise GitHubAPIError(413, "BOM artifact is too large")

        archive = self._request("GET", f"/repos/{full_name}/actions/artifacts/{artifact['id']}/zip").content
        if len(archive) > limit:
            raise GitHubAPIError(413, "BOM artifact is too large")
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            names = zf.namelist()
            name = BOM_FILENAME if BOM_FILENAME in names else next((n for n in names if n.endswith(".json")), None)
            if name is None:
                raise GitHubAPIError(422, "BOM artifact contains no JSON file")
            if zf.getinfo(name).file_size > limit:
                raise GitHubAPIError(413, "BOM file is too large")
            return json.loads(zf.read(name))
