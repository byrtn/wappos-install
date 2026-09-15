from __future__ import annotations
# Auteur : Patrick Ritaine

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
def test_cross_domain_status_route(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))

    def fake_run(cmd, **kwargs):
        return _FakeCompletedProcess(0, stdout="1\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.get("/admin/apps/roundcube/cross-domain", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"enabled": True}


@respx.mock
def test_cross_domain_enable_route(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.put(
        "/admin/apps/roundcube/cross-domain",
        json={"enabled": True},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204
    assert captured["cmd"][-2:] == ["enable", "roundcube"]


@respx.mock
def test_cross_domain_disable_route_fails_on_bad_script(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["byrtn.fr"], "main": "byrtn.fr"}))

    def fake_run(cmd, **kwargs):
        return _FakeCompletedProcess(1, stderr="App non installee")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = client.put(
        "/admin/apps/unknownapp/cross-domain",
        json={"enabled": False},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code >= 400
