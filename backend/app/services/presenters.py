from datetime import UTC, datetime, timedelta
from typing import Any

from app.models import GitHubInstallation, Scan, ScanStatus, TrackedRepository
from app.schemas.github import GitHubAccount, InstallationRead
from app.schemas.repository import PullRequestRead, RepositoryDetail, RepositoryRead, RepositoryStatus, ScanRead
from app.services.bom import component_counts

DISPATCH_GRACE = timedelta(minutes=3)


def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def latest_successful_scan(repo: TrackedRepository) -> Scan | None:
    return next((s for s in repo.scans if s.status == ScanStatus.SUCCESS and s.bom), None)


def repository_status(repo: TrackedRepository | None) -> RepositoryStatus:
    if repo is None:
        return RepositoryStatus.NOT_ENABLED
    if repo.pr_merged_at is None:
        return RepositoryStatus.PR_OPEN
    latest = repo.scans[0] if repo.scans else None
    if latest and latest.status == ScanStatus.RUNNING:
        return RepositoryStatus.SCANNING
    dispatched = as_utc(repo.scan_dispatched_at)
    if dispatched and datetime.now(UTC) - dispatched < DISPATCH_GRACE:
        return RepositoryStatus.SCANNING
    if latest_successful_scan(repo):
        return RepositoryStatus.SCANNED
    if latest and latest.status == ScanStatus.FAILURE:
        return RepositoryStatus.FAILED
    return RepositoryStatus.PENDING


def installation_read(inst: GitHubInstallation) -> InstallationRead:
    return InstallationRead(
        id=inst.id,
        account=GitHubAccount(login=inst.account_login, type=inst.account_type),
        repository_selection=inst.repository_selection,
        installed_at=as_utc(inst.created_at),
    )


def _pull_request(repo: TrackedRepository) -> PullRequestRead | None:
    if not (repo.pr_number or repo.pr_merged_at):
        return None
    return PullRequestRead(number=repo.pr_number, url=repo.pr_url, merged=repo.pr_merged_at is not None, opened_at=as_utc(repo.created_at))


def repository_read(repo: TrackedRepository | None, github: dict[str, Any] | None = None) -> RepositoryRead:
    if github is None and repo is None:
        raise ValueError("Need a tracked repository or GitHub data")
    latest = latest_successful_scan(repo) if repo else None
    if github:
        meta = {
            "id": github["id"],
            "full_name": github["full_name"],
            "description": github.get("description"),
            "language": github.get("language"),
            "private": github.get("private", True),
            "stars": github.get("stargazers_count", 0),
            "default_branch": github.get("default_branch", "main"),
            "updated_at": github.get("pushed_at"),
        }
    else:
        meta = {
            "id": repo.id,
            "full_name": repo.full_name,
            "description": repo.description,
            "language": repo.language,
            "private": repo.is_private,
            "stars": repo.stars,
            "default_branch": repo.default_branch,
            "updated_at": None,
        }
    return RepositoryRead(
        **meta,
        name=meta["full_name"].split("/", 1)[1],
        status=repository_status(repo),
        pr=_pull_request(repo) if repo else None,
        last_scan_at=as_utc(latest.finished_at) if latest else None,
        counts=component_counts(latest.bom) if latest else None,
    )


def scan_read(scan: Scan) -> ScanRead:
    return ScanRead(
        id=str(scan.id),
        status=scan.status,
        trigger=scan.trigger,
        commit_sha=scan.commit_sha,
        run_url=scan.run_url,
        started_at=as_utc(scan.started_at),
        finished_at=as_utc(scan.finished_at),
        counts=component_counts(scan.bom),
        error=scan.error,
    )


def repository_detail(repo: TrackedRepository) -> RepositoryDetail:
    return RepositoryDetail(**repository_read(repo).model_dump(), scans=[scan_read(s) for s in repo.scans])
