from __future__ import annotations
# Auteur : Patrick Ritaine

import httpx
import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError, UpstreamUnavailableError


@respx.mock
def test_login_success_extracts_session_cookie(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(
        return_value=Response(
            200,
            headers={"set-cookie": "yunohost.admin=abc123; HttpOnly; Path=/yunohost/api; Secure"},
            text="Logged in",
        )
    )

    token = admin.login("adminynh", "correct-password")

    assert token == "abc123"


@respx.mock
def test_login_missing_credentials_raises_invalid_credentials(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(400, text="Missing credentials parameter"))

    with pytest.raises(InvalidCredentialsError):
        admin.login("adminynh", "")


@respx.mock
def test_login_wrong_password_raises_invalid_credentials(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(401, text="Invalid password or username"))

    with pytest.raises(InvalidCredentialsError):
        admin.login("adminynh", "wrong-password")


@respx.mock
def test_login_success_without_cookie_raises_protocol_error(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(200, text="Logged in"))

    with pytest.raises(UpstreamProtocolError):
        admin.login("adminynh", "correct-password")


@respx.mock
def test_login_network_failure_raises_unavailable(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(UpstreamUnavailableError):
        admin.login("adminynh", "correct-password")


@respx.mock
def test_list_users_parses_real_shape_seen_on_vm203(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(
        return_value=Response(
            200,
            json={
                "users": {
                    "adminynh": {
                        "username": "adminynh",
                        "fullname": "Admin YNH",
                        "mail": "adminynh@dev.byrtn.fr",
                        "mailbox-quota": "0",
                    },
                    "patrick.ritaine": {
                        "username": "patrick.ritaine",
                        "fullname": "Patrick RITAINE",
                        "mail": "patrick.ritaine@dev.byrtn.fr",
                        "mailbox-quota": "0",
                    },
                }
            },
        )
    )

    users = admin.list_users("fake-session-token")

    assert {u.username for u in users} == {"adminynh", "patrick.ritaine"}
    assert all(u.mail.endswith("@dev.byrtn.fr") for u in users)


@respx.mock
def test_list_users_rejects_invalid_session(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_users("expired-token")


@respx.mock
def test_list_users_unexpected_shape_raises_protocol_error(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_users("fake-session-token")


@respx.mock
def test_ping_accepts_the_verified_400_shape(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(400, text="Missing credentials parameter"))

    admin.ping()


@respx.mock
def test_ping_raises_protocol_error_if_engine_behavior_changes(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(200, text="unexpected"))

    with pytest.raises(UpstreamProtocolError):
        admin.ping()
