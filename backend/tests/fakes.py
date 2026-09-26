from app.integrations.github.client import GitHubAPIError

SAMPLE_BOM = {
    "bomFormat": "CycloneDX",
    "specVersion": "1.6",
    "components": [
        {"type": "library", "name": "anthropic", "purl": "pkg:pypi/anthropic@0.42.0"},
        {"type": "machine-learning-model", "name": "claude-sonnet-5"},
    ],
    "services": [{"name": "Anthropic API"}],
}


def gh_repo(repo_id: int, name: str, pushed_at: str = "2026-09-01T00:00:00Z") -> dict:
    return {
        "id": repo_id, "full_name": f"octo/{name}", "description": None, "language": "Python", "private": True,
        "stargazers_count": 0, "default_branch": "main", "pushed_at": pushed_at,
    }


class FakeInstallationClient:
    def __init__(self, app: "FakeGitHubApp"):
        self.app = app

    def list_repositories(self):
        return self.app.repositories

    def workflow_exists(self, full_name, ref):
        return full_name in self.app.repos_with_workflow

    def open_workflow_pull_request(self, full_name, default_branch):
        if full_name in self.app.failing_repos:
            raise GitHubAPIError(403, "Resource not accessible by integration")
        self.app.calls.append(("open_pr", full_name))
        return {"number": 7, "html_url": f"https://github.com/{full_name}/pull/7"}

    def dispatch_scan(self, full_name, ref):
        self.app.calls.append(("dispatch", full_name))

    def download_bom(self, full_name, run_id):
        self.app.calls.append(("download", full_name, run_id))
        return self.app.bom


class FakeGitHubApp:
    configured = True

    def __init__(self):
        self.repositories = [gh_repo(11, "app", "2026-09-01T00:00:00Z"), gh_repo(12, "web", "2026-09-02T00:00:00Z"), gh_repo(13, "ops", "2026-08-01T00:00:00Z")]
        self.repos_with_workflow: set[str] = set()
        self.failing_repos: set[str] = set()
        self.bom = SAMPLE_BOM
        self.calls: list[tuple] = []
        self.deleted_installations: list[int] = []

    def install_url(self, state):
        return f"https://github.com/apps/bomwatcher-test/installations/new?state={state}"

    def get_installation(self, installation_id):
        if installation_id == 404:
            raise GitHubAPIError(404, "Not Found")
        return {"account": {"login": "octo", "type": "User"}, "repository_selection": "all"}

    def delete_installation(self, installation_id):
        self.deleted_installations.append(installation_id)

    def for_installation(self, installation_id):
        return FakeInstallationClient(self)
