from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_permissions_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/users/permissions")


@pytest.fixture
def admin_groups_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/users/groups")


@respx.mock
def test_list_permissions_parses_real_shape(admin_permissions_url: str) -> None:
    respx.get(admin_permissions_url).mock(
        return_value=Response(
            200,
            json={
                "permissions": {
                    "wappos_admin.main": {
                        "label": "Wappos Admin",
                        "url": "/",
                        "allowed": ["admins"],
                    }
                }
            },
        )
    )

    permissions = admin.list_permissions("fake-session-token")

    assert permissions["wappos_admin.main"].allowed == ["admins"]


@respx.mock
def test_list_permissions_requests_full_and_parses_properties(admin_permissions_url: str) -> None:
    route = respx.get(admin_permissions_url).mock(
        return_value=Response(
            200,
            json={
                "permissions": {
                    "wappos_admin.main": {
                        "label": "Wappos Admin",
                        "url": "/",
                        "allowed": ["admins"],
                        "description": "Portail d'administration",
                        "order": 3,
                        "show_tile": True,
                        "hide_from_public": False,
                        "corresponding_users": ["alice", "adminynh"],
                        "additional_urls": ["/admin-api"],
                    }
                }
            },
        )
    )

    permissions = admin.list_permissions("fake-session-token")

    assert route.calls.last.request.url.params.get("full") == ""
    perm = permissions["wappos_admin.main"]
    assert perm.description == "Portail d'administration"
    assert perm.order == 3
    assert perm.show_tile is True
    assert perm.hide_from_public is False
    assert perm.corresponding_users == ["alice", "adminynh"]
    assert perm.additional_urls == ["/admin-api"]


@respx.mock
def test_list_permissions_rejects_invalid_session(admin_permissions_url: str) -> None:
    respx.get(admin_permissions_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_permissions("expired-token")


@respx.mock
def test_update_permission_add_uses_native_path_pattern(admin_permissions_url: str) -> None:
    route = respx.put(f"{admin_permissions_url}/wappos_admin.main/add/all_users").mock(return_value=Response(200))

    admin.update_permission("fake-session-token", "wappos_admin.main", add=["all_users"])

    assert route.called


@respx.mock
def test_update_permission_add_and_remove_multiple_groups(admin_permissions_url: str) -> None:
    add_route = respx.put(f"{admin_permissions_url}/wappos_admin.main/add/visitors").mock(return_value=Response(200))
    remove_route = respx.put(f"{admin_permissions_url}/wappos_admin.main/remove/admins").mock(
        return_value=Response(200)
    )

    admin.update_permission("fake-session-token", "wappos_admin.main", add=["visitors"], remove=["admins"])

    assert add_route.called
    assert remove_route.called


@respx.mock
def test_update_permission_preserves_error_key(admin_permissions_url: str) -> None:
    respx.put(f"{admin_permissions_url}/wappos_admin.main/add/nonexistent").mock(
        return_value=Response(400, json={"error_key": "group_unknown"})
    )

    from wappos_api.errors import UpstreamValidationError

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.update_permission("fake-session-token", "wappos_admin.main", add=["nonexistent"])
    assert exc_info.value.code == "group_unknown"


@respx.mock
def test_list_groups_full_marks_special_groups_and_keeps_members_and_permissions(admin_groups_url: str) -> None:
    respx.get(admin_groups_url).mock(
        return_value=Response(
            200,
            json={
                "groups": {
                    "visitors": {"members": [], "permissions": ["wappos_portal.public"]},
                    "all_users": {"members": ["alice"], "permissions": []},
                    "admins": {"members": ["adminynh"], "permissions": ["wappos_admin.main"]},
                    "team": {"members": ["alice"], "permissions": ["wappos_admin.main"]},
                }
            },
        )
    )

    groups = {g.name: g for g in admin.list_groups_full("fake-session-token")}

    assert groups["visitors"].is_special is True
    assert groups["team"].is_special is False
    assert groups["team"].members == ["alice"]
    assert groups["admins"].permissions == ["wappos_admin.main"]


@respx.mock
def test_list_groups_full_rejects_invalid_session(admin_groups_url: str) -> None:
    respx.get(admin_groups_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_groups_full("expired-token")


@respx.mock
def test_list_groups_full_unexpected_shape_raises_protocol_error(admin_groups_url: str) -> None:
    respx.get(admin_groups_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_groups_full("fake-session-token")


@respx.mock
def test_create_group_uses_native_path_and_body(admin_groups_url: str) -> None:
    route = respx.post(admin_groups_url).mock(return_value=Response(200))

    admin.create_group("fake-session-token", "team")

    assert route.called
    assert route.calls.last.request.content == b'{"groupname":"team"}'


@respx.mock
def test_delete_group_uses_native_path(admin_groups_url: str) -> None:
    route = respx.delete(f"{admin_groups_url}/team").mock(return_value=Response(200))

    admin.delete_group("fake-session-token", "team")

    assert route.called


@respx.mock
def test_update_group_members_add_and_remove(admin_groups_url: str) -> None:
    add_route = respx.put(f"{admin_groups_url}/team/add/alice").mock(return_value=Response(200))
    remove_route = respx.put(f"{admin_groups_url}/team/remove/bob").mock(return_value=Response(200))

    admin.update_group_members("fake-session-token", "team", add=["alice"], remove=["bob"])

    assert add_route.called
    assert remove_route.called
