from __future__ import annotations
# Auteur : Patrick Ritaine

import httpx
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_health_ok_when_both_connectors_respond(portalapi_public_url: str, admin_login_url: str) -> None:
    respx.get(portalapi_public_url).mock(return_value=Response(200, json={}))
    respx.post(admin_login_url).mock(return_value=Response(400, text="Missing credentials parameter"))

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["portalapi"]["status"] == "ok"
    assert body["yunohost_api"]["status"] == "ok"


@respx.mock
def test_health_degraded_when_portalapi_is_down(portalapi_public_url: str, admin_login_url: str) -> None:
    respx.get(portalapi_public_url).mock(side_effect=httpx.ConnectError("boom"))
    respx.post(admin_login_url).mock(return_value=Response(400, text="Missing credentials parameter"))

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["portalapi"]["status"] == "unreachable"
    assert body["yunohost_api"]["status"] == "ok"


@respx.mock
def test_health_degraded_when_yunohost_api_behavior_changed(
    portalapi_public_url: str, admin_login_url: str
) -> None:
    respx.get(portalapi_public_url).mock(return_value=Response(200, json={}))
    respx.post(admin_login_url).mock(return_value=Response(200, text="unexpected"))

    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["yunohost_api"]["status"] == "unreachable"
