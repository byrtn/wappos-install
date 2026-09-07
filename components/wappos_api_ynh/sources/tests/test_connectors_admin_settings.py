from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError


@pytest.fixture
def admin_settings_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/settings")


@respx.mock
def test_get_global_settings_returns_raw_payload(admin_settings_url: str) -> None:
    respx.get(admin_settings_url).mock(
        return_value=Response(
            200,
            json={"panels": [{"id": "security", "name": "Security", "sections": []}]},
        )
    )

    data = admin.get_global_settings("fake-session-token")

    assert data["panels"][0]["id"] == "security"


@respx.mock
def test_get_global_settings_rejects_invalid_session(admin_settings_url: str) -> None:
    respx.get(admin_settings_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_global_settings("expired-token")


@respx.mock
def test_set_global_settings_calls_put(admin_settings_url: str) -> None:
    route = respx.put(f"{admin_settings_url}/security").mock(return_value=Response(200, json={}))

    admin.set_global_settings("fake-session-token", "security", "admin_strength=2")

    assert route.called


@respx.mock
def test_reset_global_setting_calls_delete(admin_settings_url: str) -> None:
    route = respx.delete(f"{admin_settings_url}/ssh_port").mock(return_value=Response(200))

    admin.reset_global_setting("fake-session-token", "ssh_port")

    assert route.called


@respx.mock
def test_reset_all_global_settings_calls_delete(admin_settings_url: str) -> None:
    route = respx.delete(admin_settings_url).mock(return_value=Response(200))

    admin.reset_all_global_settings("fake-session-token")

    assert route.called


@respx.mock
def test_get_global_setting_returns_full_metadata(admin_settings_url: str) -> None:
    route = respx.get(f"{admin_settings_url}/ssh.port").mock(
        return_value=Response(200, json={"type": "number", "value": 922})
    )

    value = admin.get_global_setting("fake-session-token", "ssh.port")

    assert value == {"type": "number", "value": 922}
    assert route.calls.last.request.url.params["full"] == ""
