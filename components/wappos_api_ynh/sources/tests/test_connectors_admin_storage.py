from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_storage_disk_list_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/storage/disk/list")


@respx.mock
def test_list_disks_parses_real_shape(admin_storage_disk_list_url: str) -> None:
    respx.get(admin_storage_disk_list_url).mock(
        return_value=Response(
            200,
            json={
                "disks": [
                    {
                        "name": "sda",
                        "model": "Samsung SSD 860",
                        "serial": "S3Z8NB0K123456",
                        "removable": False,
                        "size": "465.76 GiB",
                        "smartStatus": "SANE",
                        "type": "SSD",
                    },
                    {
                        "name": "sdb",
                        "model": "USB Flash Drive",
                        "serial": "",
                        "removable": True,
                        "size": "14.91 GiB",
                        "smartStatus": "UNKNOWN",
                        "connectionBus": "usb",
                        "type": "HDD",
                        "rpm": "Unknown",
                    },
                ]
            },
        )
    )

    disks = admin.list_disks("fake-session-token")

    assert len(disks) == 2
    assert disks[0].name == "sda"
    assert disks[0].smart_status == "SANE"
    assert disks[0].connection_bus is None
    assert disks[1].removable is True
    assert disks[1].connection_bus == "usb"
    assert disks[1].rpm == "Unknown"


@respx.mock
def test_list_disks_rejects_invalid_session(admin_storage_disk_list_url: str) -> None:
    respx.get(admin_storage_disk_list_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_disks("expired-token")


@respx.mock
def test_list_disks_unexpected_shape_raises_protocol_error(admin_storage_disk_list_url: str) -> None:
    respx.get(admin_storage_disk_list_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_disks("fake-session-token")


@respx.mock
def test_list_disks_malformed_disk_entry_raises_protocol_error(admin_storage_disk_list_url: str) -> None:
    respx.get(admin_storage_disk_list_url).mock(return_value=Response(200, json={"disks": ["not-a-dict"]}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_disks("fake-session-token")


@respx.mock
def test_get_disk_info_returns_dict(admin_login_url: str) -> None:
    disk_info_url = admin_login_url.replace("/login", "/storage/disk/info/sda")
    respx.get(disk_info_url).mock(return_value=Response(200, json={"device": "/dev/sda", "size": "500G"}))

    info = admin.get_disk_info("fake-session-token", "sda")

    assert info == {"device": "/dev/sda", "size": "500G"}
