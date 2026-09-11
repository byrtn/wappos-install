from __future__ import annotations
# Auteur : Patrick Ritaine

import json
import subprocess

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@respx.mock
def test_security_overview_route(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))
    overview = {
        "root_password": {"last_changed_epoch": 1752019200},
        "fail2ban": {"available": True, "jails": {"sshd": []}, "total_banned": 0},
        "root_ssh_keys": [
            {"bits": "256", "fingerprint": "SHA256:abc", "comment": "patrick-mint", "type": "ED25519"}
        ],
        "generated_at": 1757600000,
    }

    def fake_run(cmd, **kwargs):
        return _FakeCompletedProcess(0, stdout=json.dumps(overview))

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.get("/admin/security-overview", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == overview


@respx.mock
def test_security_overview_route_fails_on_bad_script_output(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))

    def fake_run(cmd, **kwargs):
        return _FakeCompletedProcess(1, stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.get("/admin/security-overview", headers={"X-Admin-Token": "abc123"})

    assert response.status_code >= 400
