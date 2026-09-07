from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_settings_route_returns_raw_payload(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings")
    respx.get(settings_url).mock(return_value=Response(200, json={"panels": []}))

    response = client.get("/admin/settings", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"panels": []}


@respx.mock
def test_set_settings_route_returns_json(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings/security")
    respx.put(settings_url).mock(return_value=Response(200, json={}))

    response = client.put(
        "/admin/settings/security", json={"args": "admin_strength=2"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200


@respx.mock
def test_reset_setting_route_returns_204(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings/ssh_port")
    respx.delete(settings_url).mock(return_value=Response(200))

    response = client.delete("/admin/settings/ssh_port", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_reset_all_settings_route_returns_204(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings")
    respx.delete(settings_url).mock(return_value=Response(200))

    response = client.delete("/admin/settings", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204
