from __future__ import annotations
# Auteur : Patrick Ritaine

from unittest.mock import patch

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin


@pytest.fixture
def apps_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/apps")


@respx.mock
def test_get_app_install_dir_extracts_settings_field(apps_url: str) -> None:
    respx.get(f"{apps_url}/grav").mock(
        return_value=Response(200, json={"id": "grav", "settings": {"install_dir": "/var/www/grav"}})
    )

    assert admin.get_app_install_dir("fake-session-token", "grav") == "/var/www/grav"


@respx.mock
def test_get_app_install_dir_returns_none_when_missing(apps_url: str) -> None:
    respx.get(f"{apps_url}/rspamd").mock(return_value=Response(200, json={"id": "rspamd", "settings": {}}))

    assert admin.get_app_install_dir("fake-session-token", "rspamd") is None


@respx.mock
def test_get_app_disk_usage_returns_none_when_no_install_dir(apps_url: str) -> None:
    respx.get(f"{apps_url}/rspamd").mock(return_value=Response(200, json={"id": "rspamd", "settings": {}}))

    assert admin.get_app_disk_usage("fake-session-token", "rspamd") is None


@respx.mock
def test_get_app_disk_usage_returns_none_for_unexpected_prefix(apps_url: str) -> None:
    respx.get(f"{apps_url}/weird").mock(
        return_value=Response(200, json={"id": "weird", "settings": {"install_dir": "/etc/shadow"}})
    )

    assert admin.get_app_disk_usage("fake-session-token", "weird") is None


@respx.mock
def test_get_app_disk_usage_calls_dir_size_bytes_for_allowed_prefix(apps_url: str) -> None:
    respx.get(f"{apps_url}/grav").mock(
        return_value=Response(200, json={"id": "grav", "settings": {"install_dir": "/var/www/grav"}})
    )

    with patch.object(admin, "_dir_size_bytes", return_value=123456) as mocked:
        result = admin.get_app_disk_usage("fake-session-token", "grav")

    mocked.assert_called_once_with("/var/www/grav")
    assert result == 123456
