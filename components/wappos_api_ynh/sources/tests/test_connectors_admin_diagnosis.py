from __future__ import annotations
# Auteur : Patrick Ritaine

import json

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamValidationError


@pytest.fixture
def admin_diagnosis_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/diagnosis")


@pytest.fixture
def admin_diagnosis_run_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/diagnosis/run")


@respx.mock
def test_run_diagnosis_success(admin_diagnosis_run_url: str) -> None:
    respx.put(admin_diagnosis_run_url).mock(return_value=Response(200))

    admin.run_diagnosis("fake-session-token")


@respx.mock
def test_run_diagnosis_with_category_matches_native_contract(admin_diagnosis_run_url: str) -> None:
    route = respx.put(admin_diagnosis_run_url).mock(return_value=Response(200))

    admin.run_diagnosis("fake-session-token", category="ip")

    request = route.calls.last.request
    assert "force" in request.url.params
    assert json.loads(request.content) == {"categories": ["ip"]}


@respx.mock
def test_run_diagnosis_rejects_invalid_session(admin_diagnosis_run_url: str) -> None:
    respx.put(admin_diagnosis_run_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.run_diagnosis("expired-token")


@respx.mock
def test_run_diagnosis_preserves_error_key(admin_diagnosis_run_url: str) -> None:
    respx.put(admin_diagnosis_run_url).mock(
        return_value=Response(400, json={"error_key": "diagnosis_unknown_categories"})
    )

    with pytest.raises(UpstreamValidationError) as exc_info:
        admin.run_diagnosis("fake-session-token", category="nonexistent")
    assert exc_info.value.code == "diagnosis_unknown_categories"


@respx.mock
def test_get_diagnosis_aggregates_worst_status(admin_diagnosis_url: str) -> None:
    respx.get(admin_diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "ip",
                        "description": "IP et connectivité",
                        "items": [
                            {"status": "SUCCESS", "summary": "IPv4 ok"},
                            {"status": "WARNING", "summary": "Pas d'IPv6", "details": ["détail 1"]},
                        ],
                    },
                    {
                        "id": "mail",
                        "description": "Email",
                        "items": [{"status": "SUCCESS", "summary": "Tout va bien"}],
                    },
                ]
            },
        )
    )

    reports = admin.get_diagnosis("fake-session-token")

    assert reports[0].id == "ip"
    assert reports[0].status == "WARNING"
    assert reports[1].status == "SUCCESS"


@respx.mock
def test_get_diagnosis_never_run_yet_returns_empty_list(admin_diagnosis_url: str) -> None:
    respx.get(admin_diagnosis_url).mock(
        return_value=Response(200, content=b"null", headers={"content-type": "application/json"})
    )

    reports = admin.get_diagnosis("fake-session-token")

    assert reports == []


@respx.mock
def test_get_diagnosis_rejects_invalid_session(admin_diagnosis_url: str) -> None:
    respx.get(admin_diagnosis_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_diagnosis("expired-token")


@respx.mock
def test_get_diagnosis_requests_full_and_exposes_timestamp(admin_diagnosis_url: str) -> None:
    route = respx.get(admin_diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "ip",
                        "description": "IP et connectivité",
                        "timestamp": 1754485200.0,
                        "items": [{"status": "SUCCESS", "summary": "IPv4 ok", "ignored": False}],
                    }
                ]
            },
        )
    )

    reports = admin.get_diagnosis("fake-session-token")

    assert route.calls.last.request.url.params["full"] == ""
    assert reports[0].last_execution == 1754485200.0


@respx.mock
def test_get_diagnosis_keeps_ignored_items_but_excludes_them_from_counts(admin_diagnosis_url: str) -> None:
    respx.get(admin_diagnosis_url).mock(
        return_value=Response(
            200,
            json={
                "reports": [
                    {
                        "id": "ip",
                        "description": "IP et connectivité",
                        "items": [
                            {
                                "status": "WARNING",
                                "summary": "Ignoré par l'admin",
                                "ignored": True,
                                "meta": {"test": "ipv6"},
                            },
                            {"status": "SUCCESS", "summary": "IPv4 ok", "ignored": False},
                        ],
                    }
                ]
            },
        )
    )

    reports = admin.get_diagnosis("fake-session-token")

    assert len(reports[0].items) == 2
    assert reports[0].items[0].ignored is True
    assert reports[0].items[0].meta == {"test": "ipv6"}
    assert reports[0].status == "SUCCESS"
    assert reports[0].warning_count == 0
    assert reports[0].ignored_count == 1


@respx.mock
def test_ignore_diagnosis_item_sends_filter(admin_diagnosis_url: str) -> None:
    route = respx.put(f"{admin_diagnosis_url}/ignore").mock(return_value=Response(200))

    admin.ignore_diagnosis_item("fake-session-token", "ip", {"test": "ipv6"})

    assert route.called
    assert json.loads(route.calls.last.request.content) == {"filter": ["ip", "test=ipv6"]}


@respx.mock
def test_unignore_diagnosis_item_sends_filter(admin_diagnosis_url: str) -> None:
    route = respx.put(f"{admin_diagnosis_url}/unignore").mock(return_value=Response(200))

    admin.unignore_diagnosis_item("fake-session-token", "ip", {"test": "ipv6"})

    assert route.called
    assert json.loads(route.calls.last.request.content) == {"filter": ["ip", "test=ipv6"]}
