from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import (
    InvalidCredentialsError,
    UpstreamProtocolError,
    UpstreamUnavailableError,
    UpstreamValidationError,
)


@pytest.fixture
def admin_services_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/services")


@respx.mock
def test_list_services_parses_real_shape_and_sorts(admin_services_url: str) -> None:
    route = respx.get(admin_services_url).mock(
        return_value=Response(
            200,
            json={
                "ssh": {
                    "status": "running",
                    "start_on_boot": "enabled",
                    "last_state_change": 1754485200.0,
                    "description": "Secure Shell",
                    "configuration": "unknown",
                },
                "nginx": {
                    "status": "failed",
                    "start_on_boot": "enabled",
                    "last_state_change": "unknown",
                    "description": "Web server",
                    "configuration": "broken",
                    "configuration-details": ["nginx: [emerg] bad config"],
                },
            },
        )
    )

    services = admin.list_services("fake-session-token")

    assert [s.name for s in services] == ["nginx", "ssh"]
    assert services[0].configuration == "broken"
    assert services[0].configuration_details == ["nginx: [emerg] bad config"]
    assert route.calls.last.request.headers["locale"] == "fr"
    assert services[1].status == "running"


@respx.mock
def test_list_services_rejects_invalid_session(admin_services_url: str) -> None:
    respx.get(admin_services_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_services("expired-token")


@respx.mock
def test_list_services_unexpected_shape_raises_protocol_error(admin_services_url: str) -> None:
    respx.get(admin_services_url).mock(return_value=Response(200, json=["not", "a", "dict"]))

    with pytest.raises(UpstreamProtocolError):
        admin.list_services("fake-session-token")


@respx.mock
def test_start_service_uses_native_path(admin_services_url: str) -> None:
    route = respx.put(f"{admin_services_url}/nginx/start").mock(return_value=Response(200))

    admin.start_service("fake-session-token", "nginx")

    assert route.called


@respx.mock
def test_stop_service_uses_native_path(admin_services_url: str) -> None:
    route = respx.put(f"{admin_services_url}/nginx/stop").mock(return_value=Response(200))

    admin.stop_service("fake-session-token", "nginx")

    assert route.called


@respx.mock
def test_restart_service_uses_native_path(admin_services_url: str) -> None:
    route = respx.put(f"{admin_services_url}/nginx/restart").mock(return_value=Response(200))

    admin.restart_service("fake-session-token", "nginx")

    assert route.called


@respx.mock
def test_enable_service_uses_native_path(admin_services_url: str) -> None:
    route = respx.put(f"{admin_services_url}/nginx/enable").mock(return_value=Response(200))

    admin.enable_service("fake-session-token", "nginx")

    assert route.called


@respx.mock
def test_disable_service_uses_native_path(admin_services_url: str) -> None:
    route = respx.put(f"{admin_services_url}/nginx/disable").mock(return_value=Response(200))

    admin.disable_service("fake-session-token", "nginx")

    assert route.called


@respx.mock
def test_restart_service_survives_client_timeout_when_state_matches(admin_services_url: str) -> None:
    import httpx

    respx.put(f"{admin_services_url}/sogo/restart").mock(side_effect=httpx.ReadTimeout("timed out"))
    respx.get(f"{admin_services_url}/sogo").mock(
        return_value=Response(200, json={"status": "running", "start_on_boot": "enabled"})
    )

    admin.restart_service("fake-session-token", "sogo")


@respx.mock
def test_restart_service_raises_on_client_timeout_when_state_does_not_match(admin_services_url: str) -> None:
    import httpx

    respx.put(f"{admin_services_url}/sogo/restart").mock(side_effect=httpx.ReadTimeout("timed out"))
    respx.get(f"{admin_services_url}/sogo").mock(
        return_value=Response(200, json={"status": "inactive", "start_on_boot": "enabled"})
    )

    with pytest.raises(UpstreamUnavailableError):
        admin.restart_service("fake-session-token", "sogo")


@respx.mock
def test_disable_service_survives_yunohost_diagnosis_ignore_crash(admin_services_url: str) -> None:
    respx.put(f"{admin_services_url}/nginx/disable").mock(
        return_value=Response(500, text="Traceback (most recent call last): ...")
    )
    respx.get(f"{admin_services_url}/nginx").mock(
        return_value=Response(200, json={"status": "running", "start_on_boot": "disabled"})
    )

    admin.disable_service("fake-session-token", "nginx")


@respx.mock
def test_enable_service_survives_yunohost_diagnosis_unignore_crash(admin_services_url: str) -> None:
    respx.put(f"{admin_services_url}/nginx/enable").mock(
        return_value=Response(500, text="Traceback (most recent call last): ...")
    )
    respx.get(f"{admin_services_url}/nginx").mock(
        return_value=Response(200, json={"status": "running", "start_on_boot": "enabled"})
    )

    admin.enable_service("fake-session-token", "nginx")


@respx.mock
def test_disable_service_raises_when_state_really_did_not_change(admin_services_url: str) -> None:
    respx.put(f"{admin_services_url}/nginx/disable").mock(
        return_value=Response(500, text="Traceback (most recent call last): ...")
    )
    respx.get(f"{admin_services_url}/nginx").mock(
        return_value=Response(200, json={"status": "running", "start_on_boot": "enabled"})
    )

    with pytest.raises(UpstreamProtocolError):
        admin.disable_service("fake-session-token", "nginx")


@respx.mock
def test_restart_service_raises_when_recheck_itself_fails(admin_services_url: str) -> None:
    respx.put(f"{admin_services_url}/nginx/restart").mock(return_value=Response(500))
    respx.get(f"{admin_services_url}/nginx").mock(return_value=Response(404))

    with pytest.raises(UpstreamProtocolError):
        admin.restart_service("fake-session-token", "nginx")


@respx.mock
def test_disable_service_still_raises_validation_error_with_error_key(admin_services_url: str) -> None:
    respx.put(f"{admin_services_url}/nginx/disable").mock(
        return_value=Response(400, json={"error_key": "some_business_error"})
    )

    with pytest.raises(UpstreamValidationError):
        admin.disable_service("fake-session-token", "nginx")


@respx.mock
def test_get_service_log_parses_real_shape(admin_services_url: str) -> None:
    route = respx.get(f"{admin_services_url}/nginx/log").mock(
        return_value=Response(200, json={"journalctl": ["line 1", "line 2"]})
    )

    logs = admin.get_service_log("fake-session-token", "nginx", number=50)

    assert logs == {"journalctl": ["line 1", "line 2"]}
    assert route.calls.last.request.url.params["number"] == "50"
