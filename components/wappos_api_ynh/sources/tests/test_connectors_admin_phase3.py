from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError, UpstreamValidationError


@pytest.fixture
def admin_groups_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/users/groups")


@pytest.fixture
def admin_permissions_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/users/permissions")


@respx.mock
def test_export_users_csv_returns_raw_text(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/export")
    respx.get(url).mock(return_value=Response(200, text="username;firstname\nalice;Alice\n"))

    csv_text = admin.export_users_csv("fake-session-token")

    assert "alice;Alice" in csv_text


@respx.mock
def test_export_users_csv_rejects_invalid_session(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/export")
    respx.get(url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.export_users_csv("expired-token")


@respx.mock
def test_import_users_csv_sends_multipart_with_csvfile_field(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/import")
    route = respx.post(url).mock(return_value=Response(200, json={"created": 1}))

    admin.import_users_csv("fake-session-token", "users.csv", b"username;firstname\n", update=True)

    assert route.called
    request = route.calls.last.request
    assert b'name="csvfile"' in request.content
    assert b'name="update"' in request.content
    assert b"true" in request.content


@respx.mock
def test_import_users_csv_preserves_error_key(admin_login_url: str) -> None:
    url = admin_login_url.replace("/login", "/users/import")
    respx.post(url).mock(return_value=Response(400, json={"error_key": "user_import_missing_columns"}))

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.import_users_csv("fake-session-token", "users.csv", b"bad")
    assert exc_info.value.code == "user_import_missing_columns"


@respx.mock
def test_get_group_mail_aliases_parses_real_shape(admin_groups_url: str) -> None:
    respx.get(f"{admin_groups_url}/team").mock(
        return_value=Response(200, json={"members": [], "permissions": [], "mail-aliases": ["team@dev.byrtn.fr"]})
    )

    aliases = admin.get_group_mail_aliases("fake-session-token", "team")

    assert aliases == ["team@dev.byrtn.fr"]


@respx.mock
def test_get_group_mail_aliases_unexpected_shape_raises_protocol_error(admin_groups_url: str) -> None:
    respx.get(f"{admin_groups_url}/team").mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.get_group_mail_aliases("fake-session-token", "team")


@respx.mock
def test_update_group_mailaliases_add_and_remove(admin_groups_url: str) -> None:
    add_route = respx.put(f"{admin_groups_url}/team/aliases/new@dev.byrtn.fr").mock(return_value=Response(200))
    remove_route = respx.request("DELETE", f"{admin_groups_url}/team/aliases/old@dev.byrtn.fr").mock(
        return_value=Response(200)
    )

    admin.update_group_mailaliases(
        "fake-session-token", "team", add=["new@dev.byrtn.fr"], remove=["old@dev.byrtn.fr"]
    )

    assert add_route.called
    assert remove_route.called
    import json as _json

    add_body = _json.loads(add_route.calls.last.request.content)
    assert add_body == {"groupname": "team", "aliases": ["new@dev.byrtn.fr"]}
    remove_body = _json.loads(remove_route.calls.last.request.content)
    assert remove_body == {"groupname": "team", "aliases": ["old@dev.byrtn.fr"]}


@respx.mock
def test_update_group_mailaliases_force_on_special_group(admin_groups_url: str) -> None:
    route = respx.put(f"{admin_groups_url}/all_users/aliases/all@dev.byrtn.fr").mock(return_value=Response(200))

    admin.update_group_mailaliases("fake-session-token", "all_users", add=["all@dev.byrtn.fr"], force=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"groupname": "all_users", "aliases": ["all@dev.byrtn.fr"], "force": True}


@respx.mock
def test_update_permission_properties_uses_bare_permission_route(admin_permissions_url: str) -> None:
    route = respx.put(f"{admin_permissions_url}/wappos_admin.main").mock(return_value=Response(200))

    admin.update_permission_properties("fake-session-token", "wappos_admin.main", label="Wappos Admin", order=1)

    assert route.called
    body = route.calls.last.request.content
    assert b'"label":"Wappos Admin"' in body
    assert b'"order":1' in body
    assert b'"permission":"wappos_admin.main"' in body


@respx.mock
def test_update_permission_properties_omits_none_fields(admin_permissions_url: str) -> None:
    route = respx.put(f"{admin_permissions_url}/wappos_admin.main").mock(return_value=Response(200))

    admin.update_permission_properties("fake-session-token", "wappos_admin.main", label="Wappos Admin", order=None)

    body = route.calls.last.request.content
    assert b"order" not in body


@respx.mock
def test_update_permission_properties_sends_booleans_as_strings(admin_permissions_url: str) -> None:
    route = respx.put(f"{admin_permissions_url}/wappos_admin.main").mock(return_value=Response(200))

    admin.update_permission_properties(
        "fake-session-token", "wappos_admin.main", show_tile=True, hide_from_public=False
    )

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["show_tile"] == "True"
    assert body["hide_from_public"] == "False"


@respx.mock
def test_update_permission_logo_sends_multipart_logo_field(admin_permissions_url: str) -> None:
    route = respx.put(f"{admin_permissions_url}/wappos_admin.main").mock(return_value=Response(200))

    admin.update_permission_logo("fake-session-token", "wappos_admin.main", "logo.png", b"\x89PNG...")

    assert route.called
    assert b'name="logo"' in route.calls.last.request.content
