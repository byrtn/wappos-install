from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from httpx import Response

from wappos_api.connectors import admin


@respx.mock
def test_list_services_is_cached_across_calls(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    route = respx.get(services_url).mock(
        return_value=Response(200, json={"ssh": {"status": "running", "start_on_boot": "enabled"}}),
    )

    admin.list_services("fake-session-token")
    admin.list_services("fake-session-token")

    assert route.call_count == 1


@respx.mock
def test_start_service_invalidates_the_list_services_cache(admin_login_url: str) -> None:
    services_url = admin_login_url.replace("/login", "/services")
    list_route = respx.get(services_url).mock(
        return_value=Response(200, json={"ssh": {"status": "running", "start_on_boot": "enabled"}}),
    )
    respx.put(f"{services_url}/ssh/start").mock(return_value=Response(200, json={}))

    admin.list_services("fake-session-token")
    admin.start_service("fake-session-token", "ssh")
    admin.list_services("fake-session-token")

    assert list_route.call_count == 2


@respx.mock
def test_get_diagnosis_is_cached_then_invalidated_by_run_diagnosis(admin_login_url: str) -> None:
    diagnosis_url = admin_login_url.replace("/login", "/diagnosis")
    diag_route = respx.get(diagnosis_url).mock(return_value=Response(200, json={"reports": []}))
    respx.put(f"{diagnosis_url}/run").mock(return_value=Response(200, json={}))

    admin.get_diagnosis("fake-session-token")
    admin.get_diagnosis("fake-session-token")
    assert diag_route.call_count == 1

    admin.run_diagnosis("fake-session-token")
    admin.get_diagnosis("fake-session-token")
    assert diag_route.call_count == 2
