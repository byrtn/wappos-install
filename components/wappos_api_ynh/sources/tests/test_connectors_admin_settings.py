from __future__ import annotations
# Auteur : Patrick Ritaine

import httpx
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
def test_set_global_settings_uses_heavy_timeout(admin_settings_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.put(f"{admin_settings_url}/security").mock(return_value=Response(200, json={}))
    captured = {}
    real_put = httpx.put

    def spy_put(*args, **kwargs):
        captured["timeout"] = kwargs.get("timeout")
        return real_put(*args, **kwargs)

    monkeypatch.setattr(admin.httpx, "put", spy_put)

    admin.set_global_settings("fake-session-token", "security", "admin_strength=2")

    assert captured["timeout"] == admin._HEAVY_DOMAIN_OP_TIMEOUT_SECONDS


@respx.mock
def test_get_tls_passthrough_settings_parses_panel(admin_settings_url: str) -> None:
    respx.get(admin_settings_url).mock(
        return_value=Response(
            200,
            json={
                "panels": [
                    {
                        "id": "misc",
                        "sections": [
                            {
                                "id": "tls_passthrough",
                                "options": [
                                    {"id": "tls_passthrough_enabled", "value": True},
                                    {
                                        "id": "tls_passthrough_list",
                                        "value": "dev.byrtn.fr;127.0.0.1;443,yolo.test;192.168.1.42;443",
                                    },
                                ],
                            }
                        ],
                    }
                ]
            },
        )
    )

    enabled, entries = admin.get_tls_passthrough_settings("fake-session-token")

    assert enabled is True
    assert entries == ["dev.byrtn.fr;127.0.0.1;443", "yolo.test;192.168.1.42;443"]


@respx.mock
def test_get_tls_passthrough_settings_defaults_when_section_missing(admin_settings_url: str) -> None:
    respx.get(admin_settings_url).mock(return_value=Response(200, json={"panels": []}))

    enabled, entries = admin.get_tls_passthrough_settings("fake-session-token")

    assert enabled is False
    assert entries == []


@respx.mock
def test_set_tls_passthrough_entries_writes_once_with_enabled_when_entries_present(admin_settings_url: str) -> None:
    route = respx.put(f"{admin_settings_url}/misc").mock(return_value=Response(200, json={}))

    admin.set_tls_passthrough_entries("fake-session-token", ["dev.byrtn.fr;127.0.0.1;443"])

    assert route.call_count == 1
    sent_body = route.calls[0].request.content.decode()
    assert "tls_passthrough_enabled=1" in sent_body
    assert "dev.byrtn.fr" in sent_body


@respx.mock
def test_set_tls_passthrough_entries_writes_then_disables_when_empty(admin_settings_url: str) -> None:
    route = respx.put(f"{admin_settings_url}/misc").mock(return_value=Response(200, json={}))

    admin.set_tls_passthrough_entries("fake-session-token", [])

    assert route.call_count == 2
    first_body = route.calls[0].request.content.decode()
    second_body = route.calls[1].request.content.decode()
    assert "tls_passthrough_enabled=1" in first_body
    assert "tls_passthrough_enabled=0" in second_body


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
