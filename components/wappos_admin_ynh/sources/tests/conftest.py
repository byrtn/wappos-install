# Auteur : Patrick Ritaine
import secrets
import shutil
from pathlib import Path

import pytest

import docker_gate

_SOURCES_DIR = Path(__file__).parent.parent
_PACKAGE_DIR = _SOURCES_DIR / ".package"
_PACKAGE_DIR.mkdir(exist_ok=True)
if not (_PACKAGE_DIR / "secret_key").exists():
    (_PACKAGE_DIR / "secret_key").write_text(secrets.token_hex(32))
shutil.copy(_SOURCES_DIR.parent / "manifest.toml", _PACKAGE_DIR / "manifest.toml")


@pytest.fixture(autouse=True)
def _no_real_app_endpoint_probing(monkeypatch):
    monkeypatch.setattr(docker_gate, "_probe_app_endpoint", lambda *a, **k: (True, 200))


@pytest.fixture
def client():
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def logged_in_client(client):
    with client.session_transaction() as sess:
        sess["user"] = "adminynh"
        sess["token"] = "test-token"
    return client
