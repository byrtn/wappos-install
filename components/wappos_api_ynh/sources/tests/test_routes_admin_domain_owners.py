from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.config import settings
from wappos_api.connectors import admin as admin_connector
from wappos_api.connectors import domain_owners
from wappos_api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _isolate_registry(tmp_path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(settings, "wappos_domain_owners_path", str(tmp_path / "wappos_domain_owners.json"))
    monkeypatch.setattr(settings, "wappos_domain_admin_primary_path", str(tmp_path / "wappos_domain_admin_primary.json"))


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    return token


def test_list_domain_owners_empty_by_default() -> None:
    response = client.get("/admin/domain-owners", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {}


def test_set_domain_owners_then_get() -> None:
    put_response = client.put(
        "/admin/domain-owners/dev.byrtn.fr",
        json={"owners": ["patrick", "amelle"]},
        headers={"X-Admin-Token": "abc123"},
    )

    assert put_response.status_code == 200
    assert put_response.json() == {"domain": "dev.byrtn.fr", "owners": ["amelle", "patrick"]}

    get_response = client.get("/admin/domain-owners/dev.byrtn.fr", headers={"X-Admin-Token": "abc123"})

    assert get_response.json() == {"domain": "dev.byrtn.fr", "owners": ["amelle", "patrick"]}


def test_get_domain_owners_unknown_domain_returns_empty_list() -> None:
    response = client.get("/admin/domain-owners/unknown.example", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"domain": "unknown.example", "owners": []}


def test_set_domain_owners_rejects_invalid_domain() -> None:
    response = client.put(
        "/admin/domain-owners/sub..evil.com",
        json={"owners": ["patrick"]},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 400


@respx.mock
def test_add_domain_inherits_ownership_from_parent(admin_login_url: str) -> None:
    add_domain_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_domain_url).mock(return_value=Response(200, json={}))

    client.put(
        "/admin/domain-owners/dev.byrtn.fr",
        json={"owners": ["patrick"]},
        headers={"X-Admin-Token": "abc123"},
    )

    response = client.post(
        "/admin/domains",
        json={"domain": "photography.dev.byrtn.fr"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204

    owners_response = client.get(
        "/admin/domain-owners/photography.dev.byrtn.fr", headers={"X-Admin-Token": "abc123"}
    )
    assert owners_response.json() == {"domain": "photography.dev.byrtn.fr", "owners": ["patrick"]}


def test_list_domain_owners_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domain-owners", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_get_domain_owners_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domain-owners/dev.byrtn.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_domain_admin_cannot_grant_itself_ownership_of_another_domain(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/domain-owners/dev.wappos.fr",
        json={"owners": ["domain.admin"]},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 403
    assert domain_owners.get_owners("dev.wappos.fr") == []


def test_get_primary_domain_none_by_default() -> None:
    response = client.get("/admin/domain-admins/domain.admin/primary-domain", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"username": "domain.admin", "domain": None}


def test_set_primary_domain_then_get() -> None:
    client.put(
        "/admin/domain-owners/dev.byrtn.fr", json={"owners": ["domain.admin"]}, headers={"X-Admin-Token": "abc123"}
    )

    put_response = client.put(
        "/admin/domain-admins/domain.admin/primary-domain",
        json={"domain": "dev.byrtn.fr"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert put_response.status_code == 200
    assert put_response.json() == {"username": "domain.admin", "domain": "dev.byrtn.fr"}

    get_response = client.get(
        "/admin/domain-admins/domain.admin/primary-domain", headers={"X-Admin-Token": "abc123"}
    )
    assert get_response.json() == {"username": "domain.admin", "domain": "dev.byrtn.fr"}


def test_set_primary_domain_rejects_domain_not_owned() -> None:
    response = client.put(
        "/admin/domain-admins/domain.admin/primary-domain",
        json={"domain": "dev.byrtn.fr"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 400


def test_get_primary_domain_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domain-admins/domain.admin/primary-domain", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_set_primary_domain_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/domain-admins/domain.admin/primary-domain",
        json={"domain": "dev.byrtn.fr"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 403
