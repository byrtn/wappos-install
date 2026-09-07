from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_diagnosis_returns_aggregated_reports(admin_login_url: str) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.get(diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "ip",
                        "description": "IP et connectivité",
                        "items": [{"status": "ERROR", "summary": "Pas de connexion"}],
                    }
                ]
            },
        )
    )

    response = client.get("/admin/diagnosis", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()[0]["status"] == "ERROR"


@respx.mock
def test_diagnosis_rejects_invalid_session(admin_login_url: str) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.get(diagnosis_url).mock(return_value=Response(401))

    response = client.get("/admin/diagnosis", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401


@respx.mock
def test_diagnosis_ignore_returns_updated_reports(admin_login_url: str) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.put(f"{diagnosis_url}/ignore").mock(return_value=Response(200))
    respx.get(diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "ip",
                        "description": "IP et connectivité",
                        "items": [{"status": "WARNING", "summary": "Pas d'IPv6", "ignored": True, "meta": {}}],
                    }
                ]
            },
        )
    )

    response = client.put(
        "/admin/diagnosis/ip/ignore", json={"meta": {"test": "ipv6"}}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200
    assert response.json()[0]["items"][0]["ignored"] is True


@respx.mock
def test_diagnosis_unignore_returns_updated_reports(admin_login_url: str) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.put(f"{diagnosis_url}/unignore").mock(return_value=Response(200))
    respx.get(diagnosis_url).mock(return_value=Response(200, json={"reports": []}))

    response = client.put(
        "/admin/diagnosis/ip/unignore", json={"meta": {"test": "ipv6"}}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 200


@respx.mock
def test_diagnosis_categories_returns_list(admin_login_url: str) -> None:
    categories_url = admin_login_url.replace("/login", "/diagnosis/categories")
    respx.get(categories_url).mock(return_value=Response(200, json={"categories": ["ip", "mail"]}))

    response = client.get("/admin/diagnosis/categories", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == ["ip", "mail"]
