from __future__ import annotations
# Auteur : Patrick Ritaine

import subprocess

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


class _FakeCompletedProcess:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@respx.mock
def test_login_returns_token(portalapi_login_url: str) -> None:
    respx.post(portalapi_login_url).mock(
        return_value=Response(200, headers={"set-cookie": "yunohost.portal=xyz789; Domain=.wappos.fr"})
    )

    response = client.post(
        "/portal/login",
        json={"user": "patrick.ritaine", "password": "correct-password"},
        headers={"X-Portal-Host": "wappos.fr"},
    )

    assert response.status_code == 200
    assert response.json() == {"token": "xyz789", "cookie": "yunohost.portal=xyz789; Domain=.wappos.fr"}


@respx.mock
def test_login_wrong_password_returns_401(portalapi_login_url: str) -> None:
    respx.post(portalapi_login_url).mock(return_value=Response(401))

    response = client.post(
        "/portal/login",
        json={"user": "patrick.ritaine", "password": "wrong-password"},
        headers={"X-Portal-Host": "wappos.fr"},
    )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


@respx.mock
def test_me_passes_through_yunohost_shape(portalapi_base_url: str) -> None:
    respx.get(f"{portalapi_base_url}/me").mock(
        return_value=Response(200, json={"username": "patrick.ritaine", "mail": "patrick.ritaine@wappos.fr"})
    )

    response = client.get(
        "/portal/me", headers={"X-Portal-Host": "wappos.fr", "X-Portal-Token": "xyz789"}
    )

    assert response.status_code == 200
    assert response.json()["username"] == "patrick.ritaine"


@respx.mock
def test_update_returns_204(portalapi_base_url: str) -> None:
    respx.put(f"{portalapi_base_url}/update").mock(return_value=Response(200))

    response = client.put(
        "/portal/update",
        json={"fullname": "Patrick Ritaine"},
        headers={"X-Portal-Host": "wappos.fr", "X-Portal-Token": "xyz789"},
    )

    assert response.status_code == 204


@respx.mock
def test_update_invalid_current_password_preserves_error_key(portalapi_base_url: str) -> None:
    respx.put(f"{portalapi_base_url}/update").mock(
        return_value=Response(400, json={"error_key": "invalid_password"})
    )

    response = client.put(
        "/portal/update",
        json={"currentpassword": "wrong", "newpassword": "new-strong-pass"},
        headers={"X-Portal-Host": "wappos.fr", "X-Portal-Token": "xyz789"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_password"


@respx.mock
def test_public_without_token(portalapi_public_url: str) -> None:
    respx.get(portalapi_public_url).mock(return_value=Response(200, json={"portal_public_intro": "Bienvenue"}))

    response = client.get("/portal/public", headers={"X-Portal-Host": "wappos.fr"})

    assert response.status_code == 200
    assert response.json() == {"portal_public_intro": "Bienvenue"}


def test_domains_route_returns_domain_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subprocess, "run",
        lambda cmd, **kwargs: _FakeCompletedProcess(0, stdout='{"domains": ["byrtn.fr", "wappos.lan"]}'),
    )

    response = client.get("/portal/domains")

    assert response.status_code == 200
    assert response.json() == ["byrtn.fr", "wappos.lan"]
