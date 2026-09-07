from __future__ import annotations
# Auteur : Patrick Ritaine

import io

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_export_users_returns_csv(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/export")
    respx.get(url).mock(return_value=Response(200, text="username;firstname\nalice;Alice\n"))

    response = client.get("/admin/users/export", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "alice;Alice" in response.text


@respx.mock
def test_import_users_returns_created_count(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/import")
    respx.post(url).mock(return_value=Response(200, json={"created": 1}))

    response = client.post(
        "/admin/users/import",
        files={"csvfile": ("users.csv", io.BytesIO(b"username;firstname\n"), "text/csv")},
        data={"update": "true"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 200
    assert response.json() == {"created": 1}


@respx.mock
def test_group_aliases_returns_list(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/groups/team")
    respx.get(url).mock(
        return_value=Response(200, json={"members": [], "permissions": [], "mail-aliases": ["team@dev.byrtn.fr"]})
    )

    response = client.get("/admin/groups/team/aliases", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == ["team@dev.byrtn.fr"]


@respx.mock
def test_update_group_aliases_returns_204(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/groups/team/aliases/new@dev.byrtn.fr")
    respx.put(url).mock(return_value=Response(200))

    response = client.put(
        "/admin/groups/team/aliases", json={"add": ["new@dev.byrtn.fr"]}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204


@respx.mock
def test_update_permission_properties_returns_204(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/permissions/wappos_admin.main")
    respx.put(url).mock(return_value=Response(200))

    response = client.put(
        "/admin/permissions/wappos_admin.main/properties",
        json={"label": "Wappos Admin"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_update_permission_logo_returns_204(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/permissions/wappos_admin.main")
    respx.put(url).mock(return_value=Response(200))

    response = client.put(
        "/admin/permissions/wappos_admin.main/logo",
        files={"logo": ("logo.png", io.BytesIO(b"\x89PNG..."), "image/png")},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204
