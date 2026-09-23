from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_logs_returns_list(admin_login_url: str) -> None:
    logs_url = admin_login_url.replace("/login", "/logs")
    respx.get(logs_url).mock(
        return_value=Response(
            200,
            json={
                "operation": [
                    {"name": "op1", "description": "Une opération", "success": True, "started_at": "2026-08-07"}
                ]
            },
        )
    )

    response = client.get("/admin/logs", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["name"] == "op1"


@respx.mock
def test_log_detail_returns_full_shape(admin_login_url: str) -> None:
    logs_url = admin_login_url.replace("/login", "/logs")
    respx.get(f"{logs_url}/op1").mock(
        return_value=Response(
            200,
            json={
                "name": "op1",
                "description": "Une opération",
                "metadata": {"started_at": "2026-08-07"},
                "logs": ["ligne 1"],
            },
        )
    )

    response = client.get("/admin/logs/op1", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["name"] == "op1"


@respx.mock
def test_log_share_returns_url(admin_login_url: str) -> None:
    logs_url = admin_login_url.replace("/login", "/logs")
    respx.get(f"{logs_url}/op1/share").mock(return_value=Response(200, json={"url": "https://paste.yunohost.org/abc"}))

    response = client.get("/admin/logs/op1/share", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"url": "https://paste.yunohost.org/abc"}


def _domain_admin_token(monkeypatch, owned_domains: list[str]) -> str:
    from wappos_api.connectors import admin as admin_connector

    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_logs_filtered_for_domain_admin(admin_login_url: str, monkeypatch) -> None:
    logs_url = admin_login_url.replace("/login", "/logs")
    respx.get(logs_url).mock(
        return_value=Response(
            200,
            json={
                "operation": [
                    {
                        "name": "domain_cert_install-dev.byrtn.fr",
                        "description": "x", "success": True, "started_at": "2026-08-07",
                    },
                    {
                        "name": "domain_cert_install-dev.wappos.fr",
                        "description": "y", "success": True, "started_at": "2026-08-07",
                    },
                    {"name": "settings_set", "description": "z", "success": True, "started_at": "2026-08-07"},
                ]
            },
        )
    )
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(return_value=Response(200, json={}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/logs", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert [e["name"] for e in response.json()] == ["domain_cert_install-dev.byrtn.fr"]


@respx.mock
def test_log_detail_forbidden_outside_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(return_value=Response(200, json={}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/logs/settings_set", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_log_detail_allowed_inside_scope(admin_login_url: str, monkeypatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(return_value=Response(200, json={}))
    logs_url = admin_login_url.replace("/login", "/logs")
    respx.get(f"{logs_url}/domain_cert_install-dev.byrtn.fr").mock(
        return_value=Response(
            200,
            json={
                "name": "domain_cert_install-dev.byrtn.fr",
                "description": "x",
                "metadata": {"started_at": "2026-08-07"},
                "logs": [],
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/logs/domain_cert_install-dev.byrtn.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 200
