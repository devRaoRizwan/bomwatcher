from app.integrations.github.signature import is_valid_signature
from app.integrations.github.workflow import render_workflow


def test_workflow_is_least_privilege():
    yml = render_workflow("main", "owner/repo/github-action@v1")
    assert "permissions:\n  contents: read" in yml
    assert 'branches: ["main"]' in yml
    assert "uses: owner/repo/github-action@v1" in yml
    assert "persist-credentials: false" in yml


def test_signature_check():
    assert not is_valid_signature("", b"{}", "sha256=abc")
    assert not is_valid_signature("s", b"{}", None)
    assert not is_valid_signature("s", b"{}", "sha256=abc")


def test_postgres_urls_get_psycopg_driver(monkeypatch):
    from app.core.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@db.example.com:5432/bomwatcher")
    assert Settings().database_url == "postgresql+psycopg://u:p@db.example.com:5432/bomwatcher"
