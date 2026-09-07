from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


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
def test_push_domain_dns_route_returns_diff(admin_login_url: str) -> None:
    push_url = admin_login_url.replace("/login", "/domains/dev.byrtn.fr/dns/push")
    respx.post(push_url).mock(return_value=Response(200, json={"create": [], "update": [], "delete": [], "unchanged": []}))

    response = client.post("/admin/domains/dev.byrtn.fr/dns/push", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"create": [], "update": [], "delete": [], "unchanged": []}
