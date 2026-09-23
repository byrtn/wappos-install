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


def _domain_admin_token(monkeypatch, owned_domains: list[str]) -> str:
    from wappos_api.connectors import admin as admin_connector

    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_cross_domain_add_domain_forbidden_when_app_outside_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put("/admin/apps/roundcube/cross-domain/dev.byrtn.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_cross_domain_add_domain_forbidden_when_target_outside_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put("/admin/apps/grav/cross-domain/dev.wappos.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_cross_domain_add_domain_allowed_when_both_in_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(
            200,
            json={
                "dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
                "photography.dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
            },
        )
    )
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/apps/grav/cross-domain/photography.dev.byrtn.fr", headers={"X-Admin-Token": token}
    )

    assert response.status_code == 204
    assert captured["cmd"][-3:] == ["add-domain", "grav", "photography.dev.byrtn.fr"]


@respx.mock
def test_cross_domain_remove_domain_forbidden_when_target_outside_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.request(
        "DELETE", "/admin/apps/grav/cross-domain/dev.wappos.fr", headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_cross_domain_domains_list_filtered_for_domain_admin(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )

    def fake_run(cmd, **kwargs):
        return _FakeCompletedProcess(0, stdout="dev.byrtn.fr\ndev.wappos.fr\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps/grav/cross-domain/domains", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert response.json() == ["dev.byrtn.fr"]
