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
