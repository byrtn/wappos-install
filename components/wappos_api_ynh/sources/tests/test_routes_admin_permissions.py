from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


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


@respx.mock
def test_update_group_members_returns_204(admin_login_url: str) -> None:
    groups_url = admin_login_url.replace("/login", "/users/groups")
    respx.put(f"{groups_url}/team/add/alice").mock(return_value=Response(200))

    response = client.put(
        "/admin/groups/team/members", json={"add": ["alice"]}, headers={"X-Admin-Token": "abc123"}
    )

    assert response.status_code == 204
