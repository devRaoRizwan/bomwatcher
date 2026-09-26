from enum import StrEnum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "BOMWatcher API"
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./bomwatcher.db"

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_issuer: str = "bomwatcher-api"
    jwt_audience: str = "bomwatcher-app"
    access_token_expire_minutes: int = Field(default=60, ge=5, le=24 * 60)

    auth_rate_limit_requests: int = 10
    auth_rate_limit_window_seconds: int = 60

    cors_origins: str = "http://localhost:5173"
    allowed_hosts: str = "*"

    trial_repo_limit: int = Field(default=3, ge=1)

    github_app_id: str = ""
    github_app_slug: str = ""
    github_private_key: SecretStr = SecretStr("")
    github_private_key_path: str = ""
    github_webhook_secret: SecretStr = SecretStr("")
    github_api_url: str = "https://api.github.com"
    scan_action_ref: str = "devRaoRizwan/bomwatcher/github-action@main"

    max_artifact_bytes: int = 20 * 1024 * 1024

    @field_validator("database_url")
    @classmethod
    def _use_psycopg_driver(cls, v: str) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix):]
        return v

    @field_validator("jwt_secret_key")
    @classmethod
    def _secret_strength(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters (use: openssl rand -hex 32)")
        return v

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.is_production:
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must list explicit origins in production")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Use PostgreSQL (DATABASE_URL) in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]

    @property
    def github_private_key_pem(self) -> str:
        if key := self.github_private_key.get_secret_value():
            return key.replace("\\n", "\n")
        if self.github_private_key_path:
            with open(self.github_private_key_path, encoding="utf-8") as f:
                return f.read()
        return ""

    @property
    def github_app_configured(self) -> bool:
        return bool(self.github_app_id and self.github_app_slug and self.github_private_key_pem)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
