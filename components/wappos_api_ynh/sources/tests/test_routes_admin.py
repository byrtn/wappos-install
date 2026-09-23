from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.errors import InvalidCredentialsError
from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_login_returns_token(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(
        return_value=Response(200, headers={"set-cookie": "yunohost.admin=abc123; HttpOnly"}, text="Logged in")
    )

    response = client.post("/admin/login", json={"user": "adminynh", "password": "correct-password"})

    assert response.status_code == 200
    assert response.json() == {"token": "abc123"}


@respx.mock
def test_login_wrong_password_returns_401(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.post(admin_login_url).mock(return_value=Response(401, text="Invalid password or username"))
    monkeypatch.setattr(
        admin_connector,
        "_authenticate_domain_admin",
        lambda username, password, login_domain=None: (_ for _ in ()).throw(InvalidCredentialsError("not a domain admin")),
    )

    response = client.post("/admin/login", json={"user": "adminynh", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


@respx.mock
def test_login_domain_admin_succeeds_from_primary_domain(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wappos_api.connectors import domain_owners

    respx.post(admin_login_url).mock(return_value=Response(401, text="Invalid password or username"))
    monkeypatch.setattr(admin_connector, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin_connector, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: "dev.byrtn.fr")

    response = client.post(
        "/admin/login",
        json={"user": "domain.admin", "password": "correct-password", "login_domain": "dev.byrtn.fr"},
    )

    assert response.status_code == 200
    assert response.json()["token"].startswith("da_")


@respx.mock
def test_login_domain_admin_rejected_from_other_domain(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from wappos_api.connectors import domain_owners

    respx.post(admin_login_url).mock(return_value=Response(401, text="Invalid password or username"))
    monkeypatch.setattr(admin_connector, "_ldap_group_members", lambda group: {"domain.admin"})
    monkeypatch.setattr(admin_connector, "_verify_ldap_password", lambda username, password: True)
    monkeypatch.setattr(domain_owners, "get_primary_domain", lambda username: "dev.byrtn.fr")

    response = client.post(
        "/admin/login",
        json={"user": "domain.admin", "password": "correct-password", "login_domain": "dev.wappos.fr"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


@respx.mock
def test_users_parses_real_shape(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(
        return_value=Response(
            200,
            json={
                "users": {
                    "adminynh": {"username": "adminynh", "fullname": "Admin YNH", "mail": "adminynh@dev.byrtn.fr"},
                }
            },
        )
    )

    response = client.get("/admin/users", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == [{"username": "adminynh", "fullname": "Admin YNH", "mail": "adminynh@dev.byrtn.fr"}]


@respx.mock
def test_users_rejects_invalid_session(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(return_value=Response(401))

    response = client.get("/admin/users", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


def test_session_reports_superadmin_for_regular_token() -> None:
    response = client.get("/admin/session", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"is_superadmin": True, "owned_domains": []}


def test_session_reports_domain_admin_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: ["dev.byrtn.fr"]
    )

    response = client.get("/admin/session", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert response.json() == {"is_superadmin": False, "owned_domains": ["dev.byrtn.fr"]}
