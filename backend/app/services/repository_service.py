import logging
from typing import Any

from app.core.config import Settings
from app.core.exceptions import ConflictError, NotFoundError, PlanLimitError, ServiceUnavailableError, UpstreamError
from app.db.base import utcnow
from app.integrations.github.client import GitHubAPIError, GitHubApp, InstallationClient
from app.models import GitHubInstallation, TrackedRepository, User
from app.repositories.scan_repository import ScanRepository
from app.repositories.tracked_repository_repository import TrackedRepositoryRepository
from app.schemas.repository import (
    EnableRepositoriesResponse,
    RepositoryDetail,
    RepositoryRead,
    RepositoryStatus,
    UsageRead,
)
from app.services import presenters

log = logging.getLogger(__name__)


class RepositoryService:
    def __init__(self, repos: TrackedRepositoryRepository, scans: ScanRepository, github: GitHubApp, settings: Settings):
        self.repos = repos
        self.scans = scans
        self.github = github
        self.settings = settings


    def _client(self, user: User) -> tuple[GitHubInstallation, InstallationClient]:
        if user.installation is None:
            raise ConflictError("GitHub account not connected")
        if not self.github.configured:
            raise ServiceUnavailableError("GitHub App is not configured on this server")
        return user.installation, self.github.for_installation(user.installation.id)

    def _owned(self, user: User, repository_id: int) -> TrackedRepository:
        repo = self.repos.get_for_user(repository_id, user.id)
        if repo is None:
            raise NotFoundError("Repository not found or not enabled")
        return repo

    def _visible_repositories(self, client: InstallationClient) -> list[dict[str, Any]]:
        try:
            return client.list_repositories()
        except GitHubAPIError as e:
            log.warning("Listing installation repositories failed: %s", e)
            raise UpstreamError("Could not list repositories from GitHub") from e


    def usage(self, user: User) -> UsageRead:
        return UsageRead(plan="trial", repo_limit=self.settings.trial_repo_limit, repos_enabled=self.repos.count_for_user(user.id))

    def list_repositories(self, user: User) -> list[RepositoryRead]:
        _, client = self._client(user)
        remote = sorted(self._visible_repositories(client), key=lambda r: r.get("pushed_at") or "", reverse=True)
        tracked = {r.id: r for r in self.repos.list_for_user(user.id)}
        return [presenters.repository_read(tracked.get(r["id"]), r) for r in remote]

    def get_repository(self, user: User, repository_id: int) -> RepositoryDetail:
        return presenters.repository_detail(self._owned(user, repository_id))

    def latest_bom(self, user: User, repository_id: int) -> dict[str, Any]:
        scan = presenters.latest_successful_scan(self._owned(user, repository_id))
        if scan is None:
            raise NotFoundError("No BOM available yet")
        return scan.bom

    def scan_bom(self, user: User, repository_id: int, scan_id: int) -> dict[str, Any]:
        self._owned(user, repository_id)
        scan = self.scans.get(scan_id)
        if scan is None or scan.repository_id != repository_id or not scan.bom:
            raise NotFoundError("No BOM for that scan")
        return scan.bom


    def enable(self, user: User, repository_ids: list[int]) -> EnableRepositoriesResponse:
        installation, client = self._client(user)
        tracked_ids = {r.id for r in self.repos.list_for_user(user.id)}
        new_ids = [i for i in dict.fromkeys(repository_ids) if i not in tracked_ids]
        slots_left = self.settings.trial_repo_limit - len(tracked_ids)
        if len(new_ids) > slots_left:
            raise PlanLimitError(f"Free trial allows {self.settings.trial_repo_limit} repos. You have {max(slots_left, 0)} slot(s) left.")

        visible = {r["id"]: r for r in self._visible_repositories(client)}
        opened = already_configured = 0
        errors: list[str] = []
        for repo_id in new_ids:
            remote = visible.get(repo_id)
            if remote is None:
                errors.append(f"Repository {repo_id} isn't accessible to the GitHub App")
                continue
            repo = TrackedRepository(
                id=repo_id,
                user_id=user.id,
                installation_id=installation.id,
                full_name=remote["full_name"],
                default_branch=remote["default_branch"],
                description=(remote.get("description") or "")[:1000] or None,
                language=remote.get("language"),
                is_private=remote.get("private", True),
                stars=remote.get("stargazers_count", 0),
            )
            try:
                if client.workflow_exists(repo.full_name, repo.default_branch):
                    repo.pr_merged_at = utcnow()
                    already_configured += 1
                else:
                    pr = client.open_workflow_pull_request(repo.full_name, repo.default_branch)
                    repo.pr_number, repo.pr_url = pr["number"], pr["html_url"]
                    opened += 1
            except GitHubAPIError as e:
                log.warning("Enabling %s failed: %s", repo.full_name, e)
                errors.append(f"{repo.full_name}: could not open the workflow PR ({e.status_code})")
                continue
            self.repos.add(repo)

        if errors and not (opened or already_configured):
            raise UpstreamError("; ".join(errors))
        return EnableRepositoriesResponse(opened=opened, already_configured=already_configured, errors=errors)

    def disable(self, user: User, repository_id: int) -> None:
        self.repos.delete(self._owned(user, repository_id))

    def rescan(self, user: User, repository_id: int) -> None:
        _, client = self._client(user)
        repo = self._owned(user, repository_id)
        if repo.pr_merged_at is None:
            raise ConflictError("Merge the workflow PR before scanning")
        if presenters.repository_status(repo) == RepositoryStatus.SCANNING:
            raise ConflictError("A scan is already running")
        try:
            client.dispatch_scan(repo.full_name, repo.default_branch)
        except GitHubAPIError as e:
            raise UpstreamError("GitHub refused to start the workflow") from e
        repo.scan_dispatched_at = utcnow()
        self.repos.commit()
