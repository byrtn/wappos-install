from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_permissions_returns_dict(admin_login_url: str) -> None:
    permissions_url = admin_login_url.replace("/login", "/users/permissions")
    respx.get(permissions_url).mock(
        return_value=Response(
            200,
            json={
                "permissions": {
                    "wappos_admin.main": {"label": "Wappos Admin", "url": "/", "allowed": ["admins"]}
                }
            },
        )
    )

    response = client.get("/admin/permissions", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["wappos_admin.main"]["allowed"] == ["admins"]


@respx.mock
def test_update_permission_returns_204(admin_login_url: str) -> None:
    permissions_url = admin_login_url.replace("/login", "/users/permissions")
    respx.put(f"{permissions_url}/wappos_admin.main/add/all_users").mock(return_value=Response(200))

    response = client.put(
        "/admin/permissions/wappos_admin.main",
        json={"add": ["all_users"]},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_groups_returns_list_of_group_info(admin_login_url: str) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.get(groups_url).mock(
        return_value=Response(
            200,
            json={"groups": {"admins": {"members": ["adminynh"], "permissions": []}, "all_users": {}}},
        )
    )

    response = client.get("/admin/groups", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    by_name = {g["name"]: g for g in response.json()}
    assert by_name["admins"]["members"] == ["adminynh"]
    assert by_name["admins"]["is_special"] is True


@respx.mock
def test_create_group_returns_204(admin_login_url: str) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.post(groups_url).mock(return_value=Response(200))

    response = client.post(
        "/admin/groups", json={"groupname": "team"}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204


@respx.mock
def test_delete_group_returns_204(admin_login_url: str) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.delete(f"{groups_url}/team").mock(return_value=Response(200))

    response = client.delete("/admin/groups/team", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


def test_delete_wappos_domain_admins_group_forbidden() -> None:
    response = client.delete("/admin/groups/wappos_domain_admins", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 403


@respx.mock
def test_update_group_members_returns_204(admin_login_url: str) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.put(f"{groups_url}/team/add/alice").mock(return_value=Response(200))

    response = client.put(
        "/admin/groups/team/members", json={"add": ["alice"]}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204


@respx.mock
def test_permissions_filtered_for_domain_admin(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    permissions_url = admin_login_url.replace("/login", "/users/permissions")
    respx.get(permissions_url).mock(
        return_value=Response(
            200,
            json={
                "permissions": {
                    "roundcube.main": {"label": "Roundcube", "url": "dev.byrtn.fr/webmail", "allowed": ["all_users"]},
                    "grav.main": {"label": "Grav", "url": "dev.wappos.fr/actus", "allowed": ["all_users"]},
                    "mail.main": {"label": "Mail", "url": None, "allowed": ["all_users"]},
                }
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/permissions", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert list(response.json().keys()) == ["roundcube.main"]


@respx.mock
def test_update_permission_forbidden_when_permission_outside_scope(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    permissions_url = admin_login_url.replace("/login", "/users/permissions")
    respx.get(permissions_url).mock(
        return_value=Response(
            200,
            json={"permissions": {"grav.main": {"label": "Grav", "url": "dev.wappos.fr/actus", "allowed": []}}},
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/permissions/grav.main", json={"add": ["someone"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_update_permission_forbidden_when_added_user_outside_scope(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    permissions_url = admin_login_url.replace("/login", "/users/permissions")
    respx.get(permissions_url).mock(
        return_value=Response(
            200,
            json={
                "permissions": {
                    "roundcube.main": {"label": "Roundcube", "url": "dev.byrtn.fr/webmail", "allowed": []}
                }
            },
        )
    )
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.get(groups_url).mock(return_value=Response(200, json={"groups": {}}))
    user_url = admin_login_url.replace("/login", "/users/someone")
    respx.get(user_url).mock(
        return_value=Response(200, json={"username": "someone", "fullname": "Someone", "mail": "someone@dev.wappos.fr"})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/permissions/roundcube.main", json={"add": ["someone"]}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_groups_allowed_and_filtered_for_domain_admin(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.get(groups_url).mock(
        return_value=Response(
            200,
            json={
                "groups": {
                    "team": {"members": ["patrick"], "permissions": []},
                    "admins": {"members": [], "permissions": []},
                }
            },
        )
    )
    users_url = admin_login_url.replace("/login", "/users")
    respx.get(users_url).mock(
        return_value=Response(
            200,
            json={
                "users": {
                    "patrick": {"username": "patrick", "fullname": "Patrick", "mail": "patrick@dev.byrtn.fr"}
                }
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/groups", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert [g["name"] for g in response.json()] == ["team"]


def test_create_group_forbidden_for_domain_admin_with_reserved_name(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post("/admin/groups", json={"groupname": "admins"}, headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_create_group_allowed_for_domain_admin_with_custom_name(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    create_url = admin_login_url.replace("/login", "/users/groups")
    respx.post(create_url).mock(return_value=Response(200))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post("/admin/groups", json={"groupname": "team"}, headers={"X-Admin-Token": token})

    assert response.status_code == 204
