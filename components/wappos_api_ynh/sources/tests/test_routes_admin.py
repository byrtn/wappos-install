from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


@respx.mock
def test_login_returns_token(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(
        return_value=Response(200, headers={"set-cookie": "yunohost.admin=abc123; HttpOnly"}, text="Logged in")
    )

    response = client.post("/admin/login", json={"user": "adminynh", "password": "correct-password"})

    assert response.status_code == 200
    assert response.json() == {"token": "abc123"}


@respx.mock
def test_login_wrong_password_returns_401(admin_login_url: str) -> None:
    respx.post(admin_login_url).mock(return_value=Response(401, text="Invalid password or username"))

    response = client.post("/admin/login", json={"user": "adminynh", "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"


@respx.mock
def test_users_parses_real_shape(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(
        return_value=Response(
            200,
            json={
                "users": {
                    "adminynh": {"username": "adminynh", "fullname": "Admin YNH", "mail": "adminynh@dev.byrtn.fr"},
                }
            },
        )
    )

    response = client.get("/admin/users", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == [{"username": "adminynh", "fullname": "Admin YNH", "mail": "adminynh@dev.byrtn.fr"}]


@respx.mock
def test_users_rejects_invalid_session(admin_users_url: str) -> None:
    respx.get(admin_users_url).mock(return_value=Response(401))

    response = client.get("/admin/users", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"
