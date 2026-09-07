from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_firewall_returns_rules(admin_login_url: str) -> None:
    firewall_url = admin_login_url.replace("/login", "/firewall")
    respx.get(firewall_url).mock(
        return_value=Response(
            200,
            json={"tcp": {"22": {"open": True, "upnp": False, "comment": "SSH"}}, "udp": {}, "router_forwarding_upnp": False},
        )
    )

    response = client.get("/admin/firewall", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["tcp"][0]["port"] == "22"


@respx.mock
def test_open_firewall_port_returns_204(admin_login_url: str) -> None:
    firewall_url = admin_login_url.replace("/login", "/firewall")
    respx.put(f"{firewall_url}/tcp/open/8080").mock(return_value=Response(200))

    response = client.put("/admin/firewall/tcp/8080/open", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_close_firewall_port_returns_204(admin_login_url: str) -> None:
    firewall_url = admin_login_url.replace("/login", "/firewall")
    respx.put(f"{firewall_url}/tcp/close/8080").mock(return_value=Response(200))

    response = client.put("/admin/firewall/tcp/8080/close", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_delete_firewall_port_returns_204(admin_login_url: str) -> None:
    firewall_url = admin_login_url.replace("/login", "/firewall")
    respx.put(f"{firewall_url}/tcp/delete/8080").mock(return_value=Response(200))

    response = client.request("DELETE", "/admin/firewall/tcp/8080", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_set_upnp_returns_204(admin_login_url: str) -> None:
    firewall_url = admin_login_url.replace("/login", "/firewall")
    respx.put(f"{firewall_url}/upnp/enable").mock(return_value=Response(200))

    response = client.put("/admin/firewall/upnp/true", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204
