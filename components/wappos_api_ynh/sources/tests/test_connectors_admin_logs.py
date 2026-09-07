from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_logs_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/logs")


@respx.mock
def test_list_logs_parses_real_shape(admin_logs_url: str) -> None:
    route = respx.get(admin_logs_url).mock(
        return_value=Response(
            200,
            json={
                "operation": [
                    {
                        "name": "20260807-103000-user_create",
                        "description": "Créer l'utilisateur alice",
                        "success": True,
                        "started_at": "2026-08-07 10:30:00",
                    },
                    {
                        "name": "20260807-090000-app_install",
                        "description": "Installer l'app nextcloud",
                        "success": "?",
                        "started_at": "2026-08-07 09:00:00",
                    },
                ]
            },
        )
    )

    logs = admin.list_logs("fake-session-token")

    assert route.calls.last.request.url.params["limit"] == "50"
    assert route.calls.last.request.url.params["with_details"] == ""
    assert len(logs) == 2
    assert logs[0].success is True
    assert logs[1].success == "?"


@respx.mock
def test_list_logs_rejects_invalid_session(admin_logs_url: str) -> None:
    respx.get(admin_logs_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_logs("expired-token")


@respx.mock
def test_list_logs_unexpected_shape_raises_protocol_error(admin_logs_url: str) -> None:
    respx.get(admin_logs_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_logs("fake-session-token")


@respx.mock
def test_get_log_parses_real_shape_with_suboperations(admin_logs_url: str) -> None:
    route = respx.get(f"{admin_logs_url}/20260807-103000-user_create").mock(
        return_value=Response(
            200,
            json={
                "name": "20260807-103000-user_create",
                "description": "Créer l'utilisateur alice",
                "log_path": "/var/log/.../20260807-103000-user_create.log",
                "metadata": {
                    "started_at": "2026-08-07 10:30:00",
                    "ended_at": "2026-08-07 10:30:05",
                    "error": None,
                    "suboperations": [
                        {"name": "sub1", "description": "Initialiser les permissions", "success": True},
                    ],
                },
                "logs": ["ligne 1", "ligne 2"],
            },
        )
    )

    detail = admin.get_log("fake-session-token", "20260807-103000-user_create", number=25)

    assert route.calls.last.request.url.params["filter_irrelevant"] == ""
    assert route.calls.last.request.url.params["with_suboperations"] == ""
    assert route.calls.last.request.url.params["number"] == "25"
    assert detail.error is False
    assert len(detail.suboperations) == 1
    assert detail.suboperations[0].description == "Initialiser les permissions"
    assert detail.more_logs_available is False


@respx.mock
def test_get_log_flags_error_and_truncation(admin_logs_url: str) -> None:
    respx.get(f"{admin_logs_url}/failed-op").mock(
        return_value=Response(
            200,
            json={
                "name": "failed-op",
                "description": "Une opération ratée",
                "metadata": {"error": "some error message"},
                "logs": ["ligne 1", "ligne 2", "ligne 3"],
            },
        )
    )

    detail = admin.get_log("fake-session-token", "failed-op", number=3)

    assert detail.error is True
    assert detail.more_logs_available is True


@respx.mock
def test_share_log_returns_url(admin_logs_url: str) -> None:
    respx.get(f"{admin_logs_url}/failed-op/share").mock(return_value=Response(200, json={"url": "https://paste.yunohost.org/abc"}))

    url = admin.share_log("fake-session-token", "failed-op")

    assert url == "https://paste.yunohost.org/abc"
