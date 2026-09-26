from datetime import datetime

from pydantic import Field

from app.schemas.common import Schema


class GitHubAccount(Schema):
    login: str
    type: str


class InstallationRead(Schema):
    id: int
    account: GitHubAccount
    repository_selection: str
    installed_at: datetime


class InstallUrlResponse(Schema):
    url: str


class InstallationCallback(Schema):
    installation_id: int = Field(gt=0)
    state: str = Field(min_length=1, max_length=2048)
