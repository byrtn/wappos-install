from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


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
