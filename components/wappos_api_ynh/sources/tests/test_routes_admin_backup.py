from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_backups_route_returns_list(admin_login_url: str) -> None:
    backups_url = admin_login_url.replace("/login", "/backups")
    respx.get(backups_url).mock(return_value=Response(200, json={"archives": []}))

    response = client.get("/admin/backups", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"archives": []}


@respx.mock
def test_create_backup_route_returns_200(admin_login_url: str) -> None:
    backups_url = admin_login_url.replace("/login", "/backups")
    respx.post(backups_url).mock(return_value=Response(200, json={"name": "manual"}))

    response = client.post("/admin/backups", json={"name": "manual"}, headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"name": "manual"}


@respx.mock
def test_restore_backup_route_returns_200(admin_login_url: str) -> None:
    restore_url = admin_login_url.replace("/login", "/backups/daily/restore")
    respx.put(restore_url).mock(return_value=Response(200, json={}))

    response = client.put("/admin/backups/daily/restore", json={"force": True}, headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200


@respx.mock
def test_delete_backup_route_returns_204(admin_login_url: str) -> None:
    delete_url = admin_login_url.replace("/login", "/backups/daily")
    respx.request("DELETE", delete_url).mock(return_value=Response(200))

    response = client.delete("/admin/backups/daily", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_download_backup_route_returns_bytes(admin_login_url: str) -> None:
    download_url = admin_login_url.replace("/login", "/backups/daily/download")
    respx.get(download_url).mock(
        return_value=Response(200, content=b"fake-bytes", headers={"content-type": "application/gzip"})
    )

    response = client.get("/admin/backups/daily/download", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.content == b"fake-bytes"
    assert response.headers["content-type"] == "application/gzip"
    assert "daily.tar.gz" in response.headers["content-disposition"]


@respx.mock
def test_backups_list_filtered_for_domain_admin(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    backups_url = admin_login_url.replace("/login", "/backups")
    respx.get(backups_url).mock(
        return_value=Response(200, json={"archives": {"daily": {"size": 1}, "weekly": {"size": 2}}})
    )
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {}, "apps": {"grav": {}}}))
    other_info_url = admin_login_url.replace("/login", "/backups/weekly")
    respx.get(other_info_url).mock(return_value=Response(200, json={"system": {"conf_nginx": {}}, "apps": {}}))
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/backups", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert list(response.json()["archives"].keys()) == ["daily"]


@respx.mock
def test_create_backup_forbidden_for_system_for_domain_admin(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/backups", json={"system": ["conf_nginx"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_create_backup_forbidden_for_app_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/backups", json={"apps": ["roundcube"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_create_backup_allowed_for_app_in_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    backups_url = admin_login_url.replace("/login", "/backups")
    respx.post(backups_url).mock(return_value=Response(200, json={"name": "manual"}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/backups", json={"apps": ["grav"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 200


@respx.mock
def test_backup_info_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {"conf_nginx": {}}, "apps": {}}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/backups/daily", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_delete_backup_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {}, "apps": {"roundcube": {}}}))
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.delete("/admin/backups/daily", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_restore_backup_forbidden_when_archive_outside_scope(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {"conf_nginx": {}}, "apps": {}}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/backups/daily/restore", json={"force": True}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_restore_backup_forbidden_for_system_param(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {}, "apps": {"grav": {}}}))
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/backups/daily/restore", json={"system": ["conf_nginx"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_download_backup_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    info_url = admin_login_url.replace("/login", "/backups/daily")
    respx.get(info_url).mock(return_value=Response(200, json={"system": {"conf_nginx": {}}, "apps": {}}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/backups/daily/download", headers={"X-Admin-Token": token})

    assert response.status_code == 403
