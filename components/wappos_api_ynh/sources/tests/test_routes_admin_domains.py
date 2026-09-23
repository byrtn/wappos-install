from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.config import settings
from wappos_api.connectors import admin as admin_connector
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
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_domains_certificates_route_returns_all_statuses(admin_login_url: str) -> None:
    certs_url = admin_login_url.replace("/login", "/domains/*/cert")
    respx.get(certs_url).mock(
        return_value=Response(200, json={"certificates": {
            "dev.byrtn.fr": {"CA_type": "letsencrypt", "validity": 50, "style": "success", "summary": "letsencrypt"},
        }})
    )

    response = client.get("/admin/domains/certificates", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["dev.byrtn.fr"]["validity"] == 50


@respx.mock
def test_domain_detail_route_returns_parsed_data(admin_login_url: str) -> None:
    domain_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr")
    respx.get(domain_url).mock(
        return_value=Response(
            200,
            json={
                "certificate": {"CA_type": "letsencrypt", "validity": 76, "style": "success"},
                "registrar": "ovh",
                "apps": [],
                "main": True,
                "topest_parent": None,
            },
        )
    )

    response = client.get("/admin/domains/dev.byrtn.fr", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["name"] == "dev.byrtn.fr"
    assert response.json()["certificate"]["CA_type"] == "letsencrypt"


@respx.mock
def test_domain_config_route_returns_raw_payload(admin_login_url: str) -> None:
    config_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/config")
    respx.get(config_url).mock(return_value=Response(200, json={"panels": []}))

    response = client.get("/admin/domains/dev.byrtn.fr/config", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"panels": []}


@respx.mock
def test_domain_dns_suggest_route_wraps_string(admin_login_url: str) -> None:
    dns_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/dns/suggest")
    respx.get(dns_url).mock(return_value=Response(200, json="dev.byrtn.fr. IN A 1.2.3.4"))

    response = client.get("/admin/domains/dev.byrtn.fr/dns/suggest", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"suggestion": "dev.byrtn.fr. IN A 1.2.3.4"}


@respx.mock
def test_set_domain_config_route_returns_json(admin_login_url: str) -> None:
    config_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/config/feature")
    respx.put(config_url).mock(return_value=Response(200, json={}))

    response = client.put(
        "/admin/domains/dev.byrtn.fr/config/feature",
        json={"args": "mail_in=1"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 200


@respx.mock
def test_set_main_domain_route_returns_204(admin_login_url: str) -> None:
    main_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/main")
    respx.put(main_url).mock(return_value=Response(200))

    response = client.put("/admin/domains/dev.byrtn.fr/main", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_install_domain_certificate_route_returns_204(admin_login_url: str) -> None:
    cert_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/cert")
    respx.put(cert_url).mock(return_value=Response(200))

    response = client.put("/admin/domains/dev.byrtn.fr/cert", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_renew_domain_certificate_route_returns_204(admin_login_url: str) -> None:
    renew_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/cert/renew")
    respx.put(renew_url).mock(return_value=Response(200))

    response = client.put("/admin/domains/dev.byrtn.fr/cert/renew", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_add_domain_route_returns_204(admin_login_url: str) -> None:
    add_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_url).mock(return_value=Response(200))

    response = client.post(
        "/admin/domains", json={"domain": "new.dev.byrtn.fr"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204


@respx.mock
def test_remove_domain_route_returns_204(admin_login_url: str) -> None:
    remove_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr")
    respx.delete(remove_url).mock(return_value=Response(200))

    response = client.delete("/admin/domains/dev.byrtn.fr", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_remove_domain_route_clears_ownership_registry(admin_login_url: str) -> None:
    from wappos_api.connectors import domain_owners

    domain_owners.set_owners("dev.byrtn.fr", ["adminbyrtn"])
    domain_owners.set_primary_domain("adminbyrtn", "dev.byrtn.fr")

    remove_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr")
    respx.delete(remove_url).mock(return_value=Response(200))

    response = client.delete("/admin/domains/dev.byrtn.fr", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204
    assert domain_owners.get_owners("dev.byrtn.fr") == []
    assert domain_owners.get_primary_domain("adminbyrtn") is None


@respx.mock
def test_push_domain_dns_route_returns_diff(admin_login_url: str) -> None:
    push_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/dns/push")
    respx.post(push_url).mock(return_value=Response(200, json={"create": [], "update": [], "delete": [], "unchanged": []}))

    response = client.post("/admin/domains/dev.byrtn.fr/dns/push", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"create": [], "update": [], "delete": [], "unchanged": []}


@respx.mock
def test_domains_list_filtered_for_domain_admin(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(
        return_value=Response(200, json={"domains": ["dev.byrtn.fr", "photography.dev.byrtn.fr", "dev.wappos.fr"]})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domains", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert response.json() == ["dev.byrtn.fr", "photography.dev.byrtn.fr"]


@respx.mock
def test_domain_detail_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domains/dev.wappos.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_domain_detail_allowed_inside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    domain_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr")
    respx.get(domain_url).mock(
        return_value=Response(
            200,
            json={
                "certificate": {"CA_type": "letsencrypt", "validity": 76, "style": "success"},
                "registrar": "ovh",
                "apps": [],
                "main": True,
                "topest_parent": None,
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/domains/dev.byrtn.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 200


def test_set_main_domain_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put("/admin/domains/dev.byrtn.fr/main", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_add_domain_allowed_for_strict_subdomain_of_owned_domain(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    add_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_url).mock(return_value=Response(200))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/domains", json={"domain": "photography.dev.byrtn.fr"}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 204


@respx.mock
def test_add_domain_allowed_for_unrelated_root_domain_and_auto_assigns_ownership(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wappos_api.connectors import domain_owners as domain_owners_connector

    add_url = admin_login_url.replace("/login", "/domains")
    respx.post(add_url).mock(return_value=Response(200))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])
    captured = {}
    monkeypatch.setattr(
        domain_owners_connector, "add_owner",
        lambda domain, username: captured.update(domain=domain, username=username),
    )

    response = client.post(
        "/admin/domains", json={"domain": "totally-unrelated.fr"}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 204
    assert captured == {"domain": "totally-unrelated.fr", "username": "domain.admin"}


def test_remove_domain_forbidden_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.delete("/admin/domains/dev.wappos.fr", headers={"X-Admin-Token": token})

    assert response.status_code == 403
