from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_versions_route_returns_dict(admin_login_url: str) -> None:
    versions_url = admin_login_url.replace("/login", "/versions")
    respx.get(versions_url).mock(return_value=Response(200, json={"yunohost": {"version": "12.1.0"}}))

    response = client.get("/admin/tools/versions", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"yunohost": {"version": "12.1.0"}}


@respx.mock
def test_migrations_route_returns_list(admin_login_url: str) -> None:
    migrations_url = admin_login_url.replace("/login", "/migrations")
    respx.get(migrations_url).mock(
        return_value=Response(200, json={"migrations": [
            {
                "id": "0031_terms_of_services", "number": 31, "name": "terms_of_services",
                "mode": "manual", "state": "pending", "description": "Conditions d'utilisation",
                "disclaimer": None,
            },
        ]})
    )

    response = client.get("/admin/migrations", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == "0031_terms_of_services"


@respx.mock
def test_run_migrations_route_returns_result(admin_login_url: str) -> None:
    migrations_url = admin_login_url.replace("/login", "/migrations")
    respx.put(migrations_url).mock(return_value=Response(200, json={"migrations_to_run": []}))

    response = client.put(
        "/admin/migrations", json={"accept_disclaimer": True}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200


@respx.mock
def test_reboot_route_returns_204(admin_login_url: str) -> None:
    reboot_url = admin_login_url.replace("/login", "/reboot")
    respx.put(reboot_url).mock(return_value=Response(200))

    response = client.put("/admin/tools/reboot", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_shutdown_route_returns_204(admin_login_url: str) -> None:
    shutdown_url = admin_login_url.replace("/login", "/shutdown")
    respx.put(shutdown_url).mock(return_value=Response(200))

    response = client.put("/admin/tools/shutdown", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_rootpw_route_returns_204(admin_login_url: str) -> None:
    rootpw_url = admin_login_url.replace("/login", "/rootpw")
    respx.put(rootpw_url).mock(return_value=Response(200))

    response = client.put(
        "/admin/tools/rootpw", json={"new_password": "correct-password"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204
