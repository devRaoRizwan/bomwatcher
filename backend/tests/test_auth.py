from app.core import security
from tests.conftest import API, register


def test_signup_login_and_me(client):
    res = client.post(f"{API}/auth/signup", json={"email": "  Dev@Example.com ", "password": "correct-horse"})
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "dev@example.com"
    assert "password" not in body and "password_hash" not in body

    token = client.post(f"{API}/auth/login", json={"email": "dev@example.com", "password": "correct-horse"}).json()
    assert token["token_type"] == "bearer" and token["expires_in"] > 0
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200 and me.json()["email"] == "dev@example.com"


def test_duplicate_signup_rejected(client):
    register(client)
    res = client.post(f"{API}/auth/signup", json={"email": "dev@example.com", "password": "another-pass"})
    assert res.status_code == 409


def test_signup_validation(client):
    assert client.post(f"{API}/auth/signup", json={"email": "not-an-email", "password": "correct-horse"}).status_code == 422
    res = client.post(f"{API}/auth/signup", json={"email": "a@example.com", "password": "Zq9!x"})
    assert res.status_code == 422
    assert "Zq9!x" not in res.text
    assert client.post(f"{API}/auth/signup", json={"email": "a@example.com", "password": "x" * 129}).status_code == 422


def test_login_failures_are_indistinguishable(client):
    register(client)
    wrong_pw = client.post(f"{API}/auth/login", json={"email": "dev@example.com", "password": "wrong-password"})
    no_user = client.post(f"{API}/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


def test_protected_routes_require_valid_token(client):
    assert client.get(f"{API}/auth/me").status_code == 401
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401
    state = security.create_install_state(1)
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {state}"}).status_code == 401


def test_password_is_hashed_with_argon2(client):
    register(client)
    from app.db.session import SessionLocal
    from app.repositories.user_repository import UserRepository

    with SessionLocal() as db:
        user = UserRepository(db).get_by_email("dev@example.com")
        assert user.password_hash.startswith("$argon2")


def test_login_is_rate_limited(client, monkeypatch):
    from app.api.deps import auth_rate_limit

    monkeypatch.setattr(auth_rate_limit, "max_requests", 3)
    payload = {"email": "dev@example.com", "password": "whatever-pass"}
    codes = [client.post(f"{API}/auth/login", json=payload).status_code for _ in range(4)]
    assert codes[-1] == 429
    res = client.post(f"{API}/auth/login", json=payload)
    assert "Retry-After" in res.headers


def test_security_headers(client):
    res = client.get(f"{API}/health")
    assert res.status_code == 200
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Cache-Control"] == "no-store"
