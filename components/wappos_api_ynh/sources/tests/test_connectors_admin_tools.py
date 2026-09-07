from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError


@respx.mock
def test_get_versions_returns_dict(admin_login_url: str) -> None:
    versions_url = admin_login_url.replace("/login", "/versions")
    respx.get(versions_url).mock(return_value=Response(200, json={"yunohost": {"version": "12.1.0"}}))

    result = admin.get_versions("fake-session-token")

    assert result == {"yunohost": {"version": "12.1.0"}}


@respx.mock
def test_get_versions_rejects_invalid_session(admin_login_url: str) -> None:
    versions_url = admin_login_url.replace("/login", "/versions")
    respx.get(versions_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_versions("expired-token")


@respx.mock
def test_get_available_updates_returns_dict(admin_login_url: str) -> None:
    update_url = admin_login_url.replace("/login", "/update")
    respx.get(update_url).mock(return_value=Response(200, json={"apps": [], "system": []}))

    result = admin.get_available_updates("fake-session-token")

    assert result == {"apps": [], "system": []}


@respx.mock
def test_refresh_updates_calls_put_with_body(admin_login_url: str) -> None:
    update_url = admin_login_url.replace("/login", "/update/system")
    route = respx.put(update_url).mock(return_value=Response(200, json={}))

    admin.refresh_updates("fake-session-token", target="system", no_refresh=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"target": "system", "no_refresh": True}


@respx.mock
def test_run_upgrade_calls_put_with_body(admin_login_url: str) -> None:
    upgrade_url = admin_login_url.replace("/login", "/upgrade/apps")
    route = respx.put(upgrade_url).mock(return_value=Response(200, json={}))

    admin.run_upgrade("fake-session-token", "apps")

    import json as _json

    assert _json.loads(route.calls.last.request.content) == {"target": "apps"}


@respx.mock
def test_list_migrations_parses_real_shape(admin_login_url: str) -> None:
    migrations_url = admin_login_url.replace("/login", "/migrations")
    respx.get(migrations_url).mock(
        return_value=Response(200, json={"migrations": [
            {
                "id": "0031_terms_of_services", "number": 31, "name": "terms_of_services",
                "mode": "manual", "state": "pending", "description": "Conditions d'utilisation",
                "disclaimer": "Ceci est un message informatif.",
            },
        ]})
    )

    migrations = admin.list_migrations("fake-session-token")

    assert migrations[0]["mode"] == "manual"
    assert migrations[0]["disclaimer"] == "Ceci est un message informatif."


@respx.mock
def test_run_migrations_calls_put_with_body(admin_login_url: str) -> None:
    migrations_url = admin_login_url.replace("/login", "/migrations")
    route = respx.put(migrations_url).mock(return_value=Response(200, json={}))

    admin.run_migrations("fake-session-token", accept_disclaimer=True)

    import json as _json

    assert _json.loads(route.calls.last.request.content) == {"accept_disclaimer": True}


@respx.mock
def test_run_migrations_with_targets_appends_to_url(admin_login_url: str) -> None:
    migrations_url = admin_login_url.replace("/login", "/migrations/0031_terms_of_services")
    route = respx.put(migrations_url).mock(return_value=Response(200, json={}))

    admin.run_migrations("fake-session-token", targets=["0031_terms_of_services"], accept_disclaimer=True)

    assert route.called


@respx.mock
def test_regen_conf_without_names_uses_bare_url(admin_login_url: str) -> None:
    regenconf_url = admin_login_url.replace("/login", "/regenconf")
    route = respx.put(regenconf_url).mock(return_value=Response(200, json={}))

    admin.regen_conf("fake-session-token", dry_run=True)

    import json as _json

    assert route.called
    assert _json.loads(route.calls.last.request.content) == {"dry_run": True}


@respx.mock
def test_regen_conf_with_names_uses_names_in_url_and_body(admin_login_url: str) -> None:
    regenconf_url = admin_login_url.replace("/login", "/regenconf/nginx,ssh")
    route = respx.put(regenconf_url).mock(return_value=Response(200, json={}))

    admin.regen_conf("fake-session-token", names=["nginx", "ssh"], force=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"force": True, "names": ["nginx", "ssh"]}


@respx.mock
def test_change_root_password_calls_put(admin_login_url: str) -> None:
    rootpw_url = admin_login_url.replace("/login", "/rootpw")
    route = respx.put(rootpw_url).mock(return_value=Response(200))

    admin.change_root_password("fake-session-token", "new-strong-password")

    import json as _json

    assert _json.loads(route.calls.last.request.content) == {"new_password": "new-strong-password"}


@respx.mock
def test_reboot_server_calls_put(admin_login_url: str) -> None:
    reboot_url = admin_login_url.replace("/login", "/reboot")
    route = respx.put(reboot_url).mock(return_value=Response(200))

    admin.reboot_server("fake-session-token", force=True)

    import json as _json

    assert _json.loads(route.calls.last.request.content) == {"force": True}


@respx.mock
def test_shutdown_server_calls_put(admin_login_url: str) -> None:
    shutdown_url = admin_login_url.replace("/login", "/shutdown")
    route = respx.put(shutdown_url).mock(return_value=Response(200))

    admin.shutdown_server("fake-session-token")

    assert route.called
    assert route.calls.last.request.content == b"{}"


@respx.mock
def test_run_postinstall_calls_post_with_body(admin_login_url: str) -> None:
    postinstall_url = admin_login_url.replace("/login", "/postinstall")
    route = respx.post(postinstall_url).mock(return_value=Response(200))

    admin.run_postinstall(
        "fake-session-token",
        domain="example.tld",
        username="admin",
        fullname="Admin Example",
        password="correct-password",
        i_have_read_terms_of_services=True,
    )

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {
        "domain": "example.tld",
        "username": "admin",
        "fullname": "Admin Example",
        "password": "correct-password",
        "i_have_read_terms_of_services": True,
    }
