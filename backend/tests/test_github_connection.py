from app.core import security
from tests.conftest import API, register


def connect(client, auth, installation_id=999):
    url = client.get(f"{API}/github/install-url", headers=auth).json()["url"]
    state = url.split("state=")[1]
    return client.post(f"{API}/github/installation", json={"installation_id": installation_id, "state": state}, headers=auth)


def test_connect_and_disconnect(client, auth, github):
    assert client.get(f"{API}/github/installation", headers=auth).json() is None
    res = connect(client, auth)
    assert res.status_code == 200
    assert res.json()["account"] == {"login": "octo", "type": "User"}
    assert client.get(f"{API}/github/installation", headers=auth).json()["id"] == 999

    assert client.delete(f"{API}/github/installation", headers=auth).status_code == 204
    assert github.deleted_installations == [999]
    assert client.get(f"{API}/github/installation", headers=auth).json() is None


def test_state_must_be_valid_and_belong_to_user(client, auth):
    bad = client.post(f"{API}/github/installation", json={"installation_id": 1, "state": "forged"}, headers=auth)
    assert bad.status_code == 400
    other_users_state = security.create_install_state(12345)
    res = client.post(f"{API}/github/installation", json={"installation_id": 1, "state": other_users_state}, headers=auth)
    assert res.status_code == 403
    access = auth["Authorization"].split()[1]
    assert client.post(f"{API}/github/installation", json={"installation_id": 1, "state": access}, headers=auth).status_code == 400


def test_unverifiable_installation_rejected(client, auth):
    assert connect(client, auth, installation_id=404).status_code == 400


def test_installation_cannot_be_claimed_twice(client, auth):
    assert connect(client, auth).status_code == 200
    other = register(client, "other@example.com")
    assert connect(client, other).status_code == 409
