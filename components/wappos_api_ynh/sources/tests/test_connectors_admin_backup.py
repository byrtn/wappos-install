from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError


@pytest.fixture
def admin_backups_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/backups")


@respx.mock
def test_list_backups_forwards_query_params(admin_backups_url: str) -> None:
    route = respx.get(admin_backups_url).mock(return_value=Response(200, json={"archives": ["daily-2026-08-10"]}))

    result = admin.list_backups("fake-session-token", with_info=True, human_readable=True)

    assert result == {"archives": ["daily-2026-08-10"]}
    params = route.calls.last.request.url.params
    assert params["with_info"] == ""
    assert params["human_readable"] == ""


@respx.mock
def test_list_backups_rejects_invalid_session(admin_backups_url: str) -> None:
    respx.get(admin_backups_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_backups("expired-token")


@respx.mock
def test_get_backup_info_returns_dict(admin_backups_url: str) -> None:
    respx.get(f"{admin_backups_url}/daily-2026-08-10").mock(
        return_value=Response(200, json={"created_at": "2026-08-10T08:00:00", "size": 123456})
    )

    info = admin.get_backup_info("fake-session-token", "daily-2026-08-10")

    assert info == {"created_at": "2026-08-10T08:00:00", "size": 123456}


@respx.mock
def test_create_backup_posts_only_provided_fields(admin_backups_url: str) -> None:
    route = respx.post(admin_backups_url).mock(return_value=Response(200, json={"name": "manual-2026-08-10"}))

    result = admin.create_backup("fake-session-token", name="manual-2026-08-10", apps=["grav"])

    assert result == {"name": "manual-2026-08-10"}
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"name": "manual-2026-08-10", "apps": ["grav"]}


@respx.mock
def test_create_backup_empty_body_when_nothing_specified(admin_backups_url: str) -> None:
    route = respx.post(admin_backups_url).mock(return_value=Response(200, json={}))

    admin.create_backup("fake-session-token")

    import json as _json

    assert _json.loads(route.calls.last.request.content) == {}


@respx.mock
def test_restore_backup_calls_put_with_body(admin_backups_url: str) -> None:
    route = respx.put(f"{admin_backups_url}/daily-2026-08-10/restore").mock(return_value=Response(200, json={}))

    admin.restore_backup("fake-session-token", "daily-2026-08-10", apps=["grav"], force=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"name": "daily-2026-08-10", "apps": ["grav"], "force": True}


@respx.mock
def test_delete_backup_calls_delete_with_body(admin_backups_url: str) -> None:
    route = respx.request("DELETE", f"{admin_backups_url}/daily-2026-08-10").mock(return_value=Response(200))

    admin.delete_backup("fake-session-token", "daily-2026-08-10")

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content) == {"name": "daily-2026-08-10"}


@respx.mock
def test_stream_backup_download_returns_bytes_and_content_type(admin_backups_url: str) -> None:
    respx.get(f"{admin_backups_url}/daily-2026-08-10/download").mock(
        return_value=Response(
            200,
            content=b"fake-tar-bytes",
            headers={"content-type": "application/gzip", "content-disposition": "attachment; filename=daily-2026-08-10.tar.gz"},
        )
    )

    body, content_type, content_disposition = admin.stream_backup_download("fake-session-token", "daily-2026-08-10")

    assert b"".join(body) == b"fake-tar-bytes"
    assert content_type == "application/gzip"
    assert content_disposition == "attachment; filename=daily-2026-08-10.tar.gz"
