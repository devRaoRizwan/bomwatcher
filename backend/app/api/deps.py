from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import AuthenticationError
from app.core.rate_limit import RateLimiter
from app.db.session import SessionLocal, get_db
from app.integrations.github.client import GitHubApp
from app.models import User
from app.repositories.installation_repository import InstallationRepository
from app.repositories.scan_repository import ScanRepository
from app.repositories.tracked_repository_repository import TrackedRepositoryRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.github_connection_service import GitHubConnectionService
from app.services.repository_service import RepositoryService
from app.services.webhook_service import WebhookService

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

_bearer = HTTPBearer(auto_error=False, description="Access token from POST /auth/login")

_settings = get_settings()
auth_rate_limit = RateLimiter(_settings.auth_rate_limit_requests, _settings.auth_rate_limit_window_seconds)


@lru_cache
def get_github_app() -> GitHubApp:
    return GitHubApp(get_settings())


GitHub = Annotated[GitHubApp, Depends(get_github_app)]


def get_auth_service(db: DbSession) -> AuthService:
    return AuthService(UserRepository(db))


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Not authenticated")
    return auth.user_from_token(credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_github_connection_service(db: DbSession, github: GitHub) -> GitHubConnectionService:
    return GitHubConnectionService(InstallationRepository(db), github)


def get_repository_service(db: DbSession, github: GitHub, settings: AppSettings) -> RepositoryService:
    return RepositoryService(TrackedRepositoryRepository(db), ScanRepository(db), github, settings)


def get_webhook_service(db: DbSession, github: GitHub) -> WebhookService:
    return WebhookService(db, SessionLocal, github)
