from __future__ import annotations
# Auteur : Patrick Ritaine

import httpx
import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamUnavailableError, UpstreamValidationError


@pytest.fixture
def admin_users_username_url(admin_users_url: str) -> str:
    return f"{admin_users_url}/patrick.ritaine"


@respx.mock
def test_create_user_success(admin_users_url: str) -> None:
    respx.post(admin_users_url).mock(return_value=Response(200))

    admin.create_user(
        "fake-session-token",
        username="new.user",
        domain="dev.byrtn.fr",
        password="correct-password",
        fullname="New User",
    )


@respx.mock
def test_create_user_already_exists_preserves_error_key(admin_users_url: str) -> None:
    respx.post(admin_users_url).mock(return_value=Response(400, json={"error_key": "user_already_exists"}))

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.create_user(
            "fake-session-token",
            username="adminynh",
            domain="dev.byrtn.fr",
            password="correct-password",
            fullname="Admin YNH",
        )
    assert exc_info.value.code == "user_already_exists"


@respx.mock
def test_create_user_network_failure_raises_unavailable(admin_users_url: str) -> None:
    respx.post(admin_users_url).mock(side_effect=httpx.ConnectError("boom"))

    with pytest.raises(UpstreamUnavailableError):
        admin.create_user(
            "fake-session-token",
            username="new.user",
            domain="dev.byrtn.fr",
            password="correct-password",
            fullname="New User",
        )


@respx.mock
def test_update_user_success(admin_users_username_url: str) -> None:
    respx.put(admin_users_username_url).mock(return_value=Response(200))

    admin.update_user("fake-session-token", "patrick.ritaine", fullname="Patrick Ritaine")


@respx.mock
def test_update_user_rejects_invalid_session(admin_users_username_url: str) -> None:
    respx.put(admin_users_username_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.update_user("expired-token", "patrick.ritaine", fullname="Patrick Ritaine")


@respx.mock
def test_delete_user_success(admin_users_username_url: str) -> None:
    respx.delete(admin_users_username_url).mock(return_value=Response(200))

    admin.delete_user("fake-session-token", "patrick.ritaine")


@respx.mock
def test_delete_user_unknown_preserves_error_key(admin_users_username_url: str) -> None:
    respx.delete(admin_users_username_url).mock(return_value=Response(400, json={"error_key": "user_unknown"}))

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.delete_user("fake-session-token", "patrick.ritaine")
    assert exc_info.value.code == "user_unknown"


@respx.mock
def test_get_user_parses_real_shape(admin_users_username_url: str) -> None:
    respx.get(admin_users_username_url).mock(
        return_value=Response(
            200,
            json={
                "username": "patrick.ritaine",
                "fullname": "Patrick Ritaine",
                "mail": "patrick@dev.byrtn.fr",
                "mail-aliases": ["p.ritaine@dev.byrtn.fr"],
                "mail-forward": ["patrick@gmail.com"],
                "mailbox-quota": {"limit": "500M", "use": "12M (2%)"},
            },
        )
    )

    detail = admin.get_user("fake-session-token", "patrick.ritaine")

    assert detail.mail_aliases == ["p.ritaine@dev.byrtn.fr"]
    assert detail.mail_forward == ["patrick@gmail.com"]
    assert detail.mailbox_quota_limit == "500M"
    assert detail.mailbox_quota_use == "12M (2%)"


@respx.mock
def test_get_user_rejects_invalid_session(admin_users_username_url: str) -> None:
    respx.get(admin_users_username_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_user("expired-token", "patrick.ritaine")


@respx.mock
def test_list_user_ssh_keys_uses_query_param(admin_users_url: str) -> None:
    ssh_keys_url = admin_users_url.replace("/users", "/users/ssh/keys")
    route = respx.get(ssh_keys_url).mock(
        return_value=Response(200, json={"keys": [{"key": "ssh-ed25519 AAAA... patrick-mint", "name": ""}]})
    )

    keys = admin.list_user_ssh_keys("fake-session-token", "adminynh")

    assert keys == [{"key": "ssh-ed25519 AAAA... patrick-mint", "name": ""}]
    assert route.calls.last.request.url.params["username"] == "adminynh"


@respx.mock
def test_add_user_ssh_key_posts_body(admin_users_url: str) -> None:
    ssh_key_url = admin_users_url.replace("/users", "/users/ssh/key")
    route = respx.post(ssh_key_url).mock(return_value=Response(200))

    admin.add_user_ssh_key("fake-session-token", "adminynh", "ssh-ed25519 AAAA...", comment="laptop")

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"username": "adminynh", "key": "ssh-ed25519 AAAA...", "comment": "laptop"}


@respx.mock
def test_remove_user_ssh_key_deletes_with_body(admin_users_url: str) -> None:
    ssh_key_url = admin_users_url.replace("/users", "/users/ssh/key")
    route = respx.request("DELETE", ssh_key_url).mock(return_value=Response(200))

    admin.remove_user_ssh_key("fake-session-token", "adminynh", "ssh-ed25519 AAAA...")

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"username": "adminynh", "key": "ssh-ed25519 AAAA..."}
