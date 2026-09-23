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


def _domain_admin_token(monkeypatch, owned_domains: list[str]) -> str:
    from wappos_api.connectors import admin as admin_connector

    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_diagnosis_filtered_for_domain_admin(admin_login_url, monkeypatch) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.get(diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "web",
                        "description": "Web",
                        "items": [
                            {"status": "ERROR", "summary": "x", "meta": {"domain": "dev.byrtn.fr"}},
                            {"status": "WARNING", "summary": "y", "meta": {"domain": "dev.wappos.fr"}},
                        ],
                    },
                    {
                        "id": "mail",
                        "description": "Mail",
                        "items": [{"status": "ERROR", "summary": "z", "meta": {}}],
                    },
                ]
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/diagnosis", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    body = response.json()
    assert [r["id"] for r in body] == ["web"]
    assert len(body[0]["items"]) == 1
    assert body[0]["items"][0]["meta"]["domain"] == "dev.byrtn.fr"


@respx.mock
def test_diagnosis_categories_filtered_for_domain_admin(admin_login_url, monkeypatch) -> None:
    categories_url = admin_login_url.replace("/login", "/diagnosis/categories")
    respx.get(categories_url).mock(
        return_value=Response(200, json={"categories": ["ip", "mail", "web", "dnsrecords"]})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/diagnosis/categories", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert sorted(response.json()) == ["dnsrecords", "web"]


def test_diagnosis_run_forbidden_for_non_scopable_category(monkeypatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post("/admin/diagnosis/run", params={"category": "mail"}, headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_diagnosis_run_forbidden_without_category_for_domain_admin(monkeypatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post("/admin/diagnosis/run", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_diagnosis_ignore_forbidden_for_non_scopable_category(monkeypatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/diagnosis/mail/ignore", json={"meta": {"domain": "dev.byrtn.fr"}}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


def test_diagnosis_ignore_forbidden_for_item_outside_scope(monkeypatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/diagnosis/web/ignore", json={"meta": {"domain": "dev.wappos.fr"}}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_diagnosis_ignore_allowed_for_item_in_scope(admin_login_url, monkeypatch) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    respx.put(f"{diagnosis_url}/ignore").mock(return_value=Response(200))
    respx.get(diagnosis_url).mock(return_value=Response(200, json={"reports": []}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/diagnosis/web/ignore", json={"meta": {"domain": "dev.byrtn.fr"}}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 200
