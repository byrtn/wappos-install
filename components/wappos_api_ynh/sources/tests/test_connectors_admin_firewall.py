from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError, UpstreamValidationError


@pytest.fixture
def admin_firewall_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/firewall")


@respx.mock
def test_list_firewall_requests_raw_and_parses_shape(admin_firewall_url: str) -> None:
    route = respx.get(admin_firewall_url).mock(
        return_value=Response(
            200,
            json={
                "tcp": {"22": {"open": True, "upnp": False, "comment": "SSH"}},
                "udp": {"53": {"open": True, "upnp": True, "comment": ""}},
                "router_forwarding_upnp": True,
            },
        )
    )

    rules = admin.list_firewall("fake-session-token")

    assert route.calls.last.request.url.params["raw"] == ""
    assert rules.tcp[0].port == "22"
    assert rules.tcp[0].comment == "SSH"
    assert rules.udp[0].upnp is True
    assert rules.upnp_enabled is True


@respx.mock
def test_list_firewall_rejects_invalid_session(admin_firewall_url: str) -> None:
    respx.get(admin_firewall_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_firewall("expired-token")


@respx.mock
def test_list_firewall_unexpected_shape_raises_protocol_error(admin_firewall_url: str) -> None:
    respx.get(admin_firewall_url).mock(return_value=Response(200, json={"tcp": "not-a-dict"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_firewall("fake-session-token")


@respx.mock
def test_open_firewall_port_sends_comment_and_upnp(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/tcp/open/8080").mock(return_value=Response(200))

    admin.open_firewall_port("fake-session-token", "tcp", 8080, comment="Test", upnp=True)

    assert route.called
    assert route.calls.last.request.url.params["comment"] == "Test"
    assert route.calls.last.request.url.params["upnp"] == ""


@respx.mock
def test_open_firewall_port_omits_upnp_when_false(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/tcp/open/8080").mock(return_value=Response(200))

    admin.open_firewall_port("fake-session-token", "tcp", 8080)

    assert "upnp" not in route.calls.last.request.url.params


@respx.mock
def test_close_firewall_port_uses_native_path(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/tcp/close/8080").mock(return_value=Response(200))

    admin.close_firewall_port("fake-session-token", "tcp", 8080)

    assert route.called


@respx.mock
def test_delete_firewall_port_uses_native_path(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/tcp/delete/8080").mock(return_value=Response(200))

    admin.delete_firewall_port("fake-session-token", "tcp", 8080)

    assert route.called


@respx.mock
def test_set_upnp_enable(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/upnp/enable").mock(return_value=Response(200))

    admin.set_upnp("fake-session-token", True)

    assert route.called


@respx.mock
def test_set_upnp_disable(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/upnp/disable").mock(return_value=Response(200))

    admin.set_upnp("fake-session-token", False)

    assert route.called


@respx.mock
def test_set_upnp_enable_failure_maps_to_upnp_port_open_failed(admin_firewall_url: str) -> None:
    respx.put(f"{admin_firewall_url}/upnp/enable").mock(
        return_value=Response(500, json={"error": "Unable to configure port forwarding using UPnP"})
    )

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.set_upnp("fake-session-token", True)

    assert exc_info.value.code == "upnp_port_open_failed"


@respx.mock
def test_set_upnp_disable_failure_uses_generic_error(admin_firewall_url: str) -> None:
    respx.put(f"{admin_firewall_url}/upnp/disable").mock(return_value=Response(500, json={"unexpected": True}))

    with pytest.raises(UpstreamProtocolError):
        admin.set_upnp("fake-session-token", False)


@respx.mock
def test_allow_firewall_uses_native_path_no_body(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/TCP/allow/8080").mock(return_value=Response(204))

    admin.allow_firewall("fake-session-token", "TCP", 8080, ipv4_only=True)

    assert route.called
    assert route.calls.last.request.content == b""
    assert route.calls.last.request.url.params["ipv4_only"] == ""


@respx.mock
def test_disallow_firewall_uses_native_path_no_body(admin_firewall_url: str) -> None:
    route = respx.put(f"{admin_firewall_url}/TCP/disallow/8080").mock(return_value=Response(204))

    admin.disallow_firewall("fake-session-token", "TCP", 8080)

    assert route.called
    assert route.calls.last.request.content == b""
