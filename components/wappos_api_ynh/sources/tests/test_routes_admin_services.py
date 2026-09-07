from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_services_returns_list(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.get(services_url).mock(
        return_value=Response(
            200, json={"nginx": {"status": "running", "start_on_boot": "enabled", "description": "Web server"}}
        )
    )

    response = client.get("/admin/services", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "nginx"


@respx.mock
def test_start_service_returns_204(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.put(f"{services_url}/nginx/start").mock(return_value=Response(200))

    response = client.put("/admin/services/nginx/start", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_stop_service_returns_204(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.put(f"{services_url}/nginx/stop").mock(return_value=Response(200))

    response = client.put("/admin/services/nginx/stop", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_restart_service_returns_204(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.put(f"{services_url}/nginx/restart").mock(return_value=Response(200))

    response = client.put("/admin/services/nginx/restart", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_enable_service_returns_204(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.put(f"{services_url}/nginx/enable").mock(return_value=Response(200))

    response = client.put("/admin/services/nginx/enable", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_disable_service_returns_204(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.put(f"{services_url}/nginx/disable").mock(return_value=Response(200))

    response = client.put("/admin/services/nginx/disable", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_service_log_returns_dict(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    respx.get(f"{services_url}/nginx/log").mock(return_value=Response(200, json={"journalctl": ["line 1"]}))

    response = client.get("/admin/services/nginx/log", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"journalctl": ["line 1"]}
