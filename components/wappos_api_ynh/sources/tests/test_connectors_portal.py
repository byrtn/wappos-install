from __future__ import annotations
# Auteur : Patrick Ritaine

import httpx
import pytest
import respx
from httpx import Response

from wappos_api.connectors import portal
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError, UpstreamUnavailableError


@respx.mock
def test_login_success_extracts_session_cookie(portalapi_login_url: str) -> None:
    respx.post(portalapi_login_url).mock(
        return_value=Response(
            200,
            headers={"set-cookie": "yunohost.portal=xyz789; Domain=.wappos.fr; HttpOnly"},
        )
    )

    token, cookie_header = portal.login("wappos.fr", "patrick.ritaine", "correct-password")

    assert token == "xyz789"
    assert cookie_header == "yunohost.portal=xyz789; Domain=.wappos.fr; HttpOnly"


@respx.mock
def test_login_wrong_password_raises_invalid_credentials(portalapi_login_url: str) -> None:
    respx.post(portalapi_login_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        portal.login("wappos.fr", "patrick.ritaine", "wrong-password")


@respx.mock
def test_login_network_failure_raises_unavailable(portalapi_login_url: str) -> None:
    respx.post(portalapi_login_url).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(UpstreamUnavailableError):
        portal.login("wappos.fr", "patrick.ritaine", "correct-password")


@respx.mock
def test_public_does_not_require_a_token(portalapi_public_url: str) -> None:
    respx.get(portalapi_public_url).mock(
        return_value=Response(200, json={"portal_public_intro": "Bienvenue"})
    )

    result = portal.public("wappos.fr")

    assert result == {"portal_public_intro": "Bienvenue"}


@respx.mock
def test_ping_uses_public_and_succeeds(portalapi_public_url: str) -> None:
    respx.get(portalapi_public_url).mock(return_value=Response(200, json={}))

    portal.ping("wappos.fr")


@respx.mock
def test_ping_raises_when_portalapi_errors(portalapi_public_url: str) -> None:
    respx.get(portalapi_public_url).mock(return_value=Response(500))

    with pytest.raises(UpstreamProtocolError):
        portal.ping("wappos.fr")


@respx.mock
def test_login_normalizes_bare_ip_host_to_current_host(
    portalapi_login_url: str, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    current_host_file = tmp_path / "current_host"
    current_host_file.write_text("dev.byrtn.fr\n")
    monkeypatch.setattr(portal, "_CURRENT_HOST_FILE", current_host_file)

    route = respx.post(portalapi_login_url).mock(
        return_value=Response(200, headers={"set-cookie": "yunohost.portal=xyz789; Domain=.dev.byrtn.fr; HttpOnly"})
    )

    portal.login("192.168.1.203", "claudeynh", "correct-password")

    assert route.calls.last.request.headers["host"] == "dev.byrtn.fr"


@respx.mock
def test_login_leaves_real_domain_host_unchanged(portalapi_login_url: str) -> None:
    route = respx.post(portalapi_login_url).mock(
        return_value=Response(200, headers={"set-cookie": "yunohost.portal=xyz789; Domain=.wappos.fr; HttpOnly"})
    )

    portal.login("wappos.fr", "patrick.ritaine", "correct-password")

    assert route.calls.last.request.headers["host"] == "wappos.fr"
