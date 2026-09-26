import os
import tempfile

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL=f"sqlite:///{_db_file.name}",
    JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters",
    GITHUB_APP_ID="1",
    GITHUB_APP_SLUG="bomwatcher-test",
    GITHUB_PRIVATE_KEY="unused-in-tests",
    GITHUB_WEBHOOK_SECRET="webhook-secret",
    TRIAL_REPO_LIMIT="2",
    AUTH_RATE_LIMIT_REQUESTS="1000",
)

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from app.api.deps import auth_rate_limit, get_github_app
from app.db.base import Base
from app.db.session import engine
from app.main import app
from tests.fakes import FakeGitHubApp

API = "/api/v1"


@pytest.fixture(autouse=True)
def _fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    auth_rate_limit.reset()
    yield


@pytest.fixture
def github() -> FakeGitHubApp:
    fake = FakeGitHubApp()
    app.dependency_overrides[get_github_app] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_github_app, None)


@pytest.fixture
def client(github) -> TestClient:
    with TestClient(app, base_url="http://testserver") as c:
        yield c


def register(client: TestClient, email: str = "dev@example.com", password: str = "correct-horse") -> dict[str, str]:
    assert client.post(f"{API}/auth/signup", json={"email": email, "password": password}).status_code == 201
    token = client.post(f"{API}/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth(client) -> dict[str, str]:
    return register(client)


def send_webhook(client: TestClient, event: str, payload: dict, secret: str = "webhook-secret"):
    body = json.dumps(payload).encode()
    signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        f"{API}/webhooks/github",
        content=body,
        headers={"X-GitHub-Event": event, "X-Hub-Signature-256": signature, "Content-Type": "application/json"},
    )
