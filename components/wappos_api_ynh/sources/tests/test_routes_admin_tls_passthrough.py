from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


def _settings_payload(enabled: bool, entries: list[str]) -> dict:
    return {
        "panels": [
            {
                "id": "misc",
                "sections": [
                    {
                        "id": "tls_passthrough",
                        "options": [
                            {"id": "tls_passthrough_enabled", "value": enabled},
                            {"id": "tls_passthrough_list", "value": ",".join(entries)},
                        ],
                    }
                ],
            }
        ]
    }


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_tls_passthrough_returns_all_entries_for_superadmin(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings")
    respx.get(settings_url).mock(
        return_value=Response(
            200, json=_settings_payload(True, ["dev.byrtn.fr;192.168.1.42;443", "dev.wappos.fr;10.0.0.5;8443"])
        )
    )

    response = client.get("/admin/tls-passthrough", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    body = response.json()
    assert body["enabled"] is True
    assert [e["domain"] for e in body["entries"]] == ["dev.byrtn.fr", "dev.wappos.fr"]


def test_tls_passthrough_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/tls-passthrough", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_update_tls_passthrough_returns_204_for_superadmin(admin_login_url: str) -> None:
    settings_url = admin_login_url.replace("/login", "/settings")
    respx.get(settings_url).mock(return_value=Response(200, json=_settings_payload(False, [])))
    respx.put(f"{settings_url}/misc").mock(return_value=Response(200, json={}))

    response = client.put(
        "/admin/tls-passthrough",
        json={"entries": [{"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": 443}]},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


def test_update_tls_passthrough_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/tls-passthrough",
        json={"entries": [{"domain": "dev.byrtn.fr", "destination": "127.0.0.1", "port": 443}]},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 403
