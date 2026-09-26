from datetime import datetime
from enum import StrEnum

from pydantic import Field

from app.schemas.common import Schema


class RepositoryStatus(StrEnum):
    NOT_ENABLED = "not_enabled"
    PR_OPEN = "pr_open"
    PENDING = "pending"
    SCANNING = "scanning"
    SCANNED = "scanned"
    FAILED = "failed"


class ComponentCounts(Schema):
    libraries: int
    models: int
    services: int


class PullRequestRead(Schema):
    number: int | None
    url: str | None
    merged: bool
    opened_at: datetime | None


class RepositoryRead(Schema):
    id: int
    name: str
    full_name: str
    description: str | None
    language: str | None
    private: bool
    stars: int
    default_branch: str
    updated_at: datetime | None
    status: RepositoryStatus
    pr: PullRequestRead | None
    last_scan_at: datetime | None
    counts: ComponentCounts | None


class ScanRead(Schema):
    id: str
    status: str
    trigger: str
    commit_sha: str
    run_url: str | None
    started_at: datetime
    finished_at: datetime | None
    counts: ComponentCounts | None
    error: str | None


class RepositoryDetail(RepositoryRead):
    scans: list[ScanRead]


class UsageRead(Schema):
    plan: str
    repo_limit: int
    repos_enabled: int


class EnableRepositoriesRequest(Schema):
    repo_ids: list[int] = Field(min_length=1, max_length=100)


class EnableRepositoriesResponse(Schema):
    opened: int
    already_configured: int
    errors: list[str]
