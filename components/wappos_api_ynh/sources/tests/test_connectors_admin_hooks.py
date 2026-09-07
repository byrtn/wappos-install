from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError


@pytest.fixture
def admin_hooks_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/hooks")


@respx.mock
def test_list_hooks_returns_list(admin_hooks_url: str) -> None:
    respx.get(f"{admin_hooks_url}/post_app_install").mock(
        return_value=Response(200, json={"hooks": ["01-nginx", "02-firewall"]})
    )

    hooks = admin.list_hooks("fake-session-token", "post_app_install")

    assert hooks == ["01-nginx", "02-firewall"]


@respx.mock
def test_list_hooks_rejects_invalid_session(admin_hooks_url: str) -> None:
    respx.get(f"{admin_hooks_url}/post_app_install").mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_hooks("expired-token", "post_app_install")
