from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_create_user_returns_204(admin_users_url: str) -> None:
    respx.post(admin_users_url).mock(return_value=Response(200))

    response = client.post(
        "/admin/users",
        json={
            "username": "new.user",
            "domain": "dev.byrtn.fr",
            "password": "correct-password",
            "fullname": "New User",
        },
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_create_user_already_exists_returns_400_with_code(admin_users_url: str) -> None:
    respx.post(admin_users_url).mock(return_value=Response(400, json={"error_key": "user_already_exists"}))

    response = client.post(
        "/admin/users",
        json={
            "username": "adminynh",
            "domain": "dev.byrtn.fr",
            "password": "correct-password",
            "fullname": "Admin YNH",
        },
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "user_already_exists"


@respx.mock
def test_update_user_only_sends_provided_fields(admin_users_url: str) -> None:
    route = respx.put(f"{admin_users_url}/patrick.ritaine").mock(return_value=Response(200))

    response = client.put(
        "/admin/users/patrick.ritaine",
        json={"fullname": "Patrick Ritaine"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204
    sent_body = route.calls.last.request.content
    import json as _json

    assert _json.loads(sent_body) == {"fullname": "Patrick Ritaine", "username": "patrick.ritaine"}


@respx.mock
def test_delete_user_returns_204(admin_users_url: str) -> None:
    respx.delete(f"{admin_users_url}/patrick.ritaine").mock(return_value=Response(200))

    response = client.delete("/admin/users/patrick.ritaine", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_user_detail_returns_full_shape(admin_users_url: str) -> None:
    respx.get(f"{admin_users_url}/patrick.ritaine").mock(
        return_value=Response(
            200,
            json={
                "username": "patrick.ritaine",
                "fullname": "Patrick Ritaine",
                "mail": "patrick@dev.byrtn.fr",
                "mail-aliases": [],
                "mail-forward": [],
                "mailbox-quota": {"limit": "0", "use": "0"},
            },
        )
    )

    response = client.get("/admin/users/patrick.ritaine", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["username"] == "patrick.ritaine"


@respx.mock
def test_export_route_not_shadowed_by_username_route(admin_users_url: str) -> None:
    respx.get(f"{admin_users_url}/export").mock(return_value=Response(200, text="username;firstname\n"))

    response = client.get("/admin/users/export", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")


@respx.mock
def test_ssh_keys_route_returns_list(admin_users_url: str) -> None:
    ssh_keys_url = admin_users_url.replace("/users", "/users/ssh/keys")
    respx.get(ssh_keys_url).mock(
        return_value=Response(200, json={"keys": [{"key": "ssh-ed25519 AAAA...", "name": "laptop"}]})
    )

    response = client.get("/admin/users/adminynh/ssh-keys", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == [{"key": "ssh-ed25519 AAAA...", "name": "laptop"}]


@respx.mock
def test_add_ssh_key_route_returns_204(admin_users_url: str) -> None:
    ssh_key_url = admin_users_url.replace("/users", "/users/ssh/key")
    respx.post(ssh_key_url).mock(return_value=Response(200))

    response = client.post(
        "/admin/users/adminynh/ssh-keys",
        json={"key": "ssh-ed25519 AAAA...", "comment": "laptop"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_remove_ssh_key_route_returns_204(admin_users_url: str) -> None:
    ssh_key_url = admin_users_url.replace("/users", "/users/ssh/key")
    respx.request("DELETE", ssh_key_url).mock(return_value=Response(200))

    response = client.request(
        "DELETE",
        "/admin/users/adminynh/ssh-keys",
        json={"key": "ssh-ed25519 AAAA..."},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_users_list_filtered_for_domain_admin(admin_users_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    respx.get(admin_users_url).mock(
        return_value=Response(
            200,
            json={
                "users": {
                    "patrick": {"username": "patrick", "fullname": "Patrick", "mail": "patrick@dev.byrtn.fr"},
                    "someone": {"username": "someone", "fullname": "Someone", "mail": "someone@dev.wappos.fr"},
                }
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/users", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert [u["username"] for u in response.json()] == ["patrick"]


def test_create_user_forbidden_for_domain_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/users",
        json={"username": "new.user", "domain": "dev.wappos.fr", "password": "correct-password", "fullname": "New"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 403


@respx.mock
def test_user_detail_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    user_url = admin_login_url.replace("/login", "/users/someone")
    respx.get(user_url).mock(
        return_value=Response(200, json={"username": "someone", "fullname": "Someone", "mail": "someone@dev.wappos.fr"})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/users/someone", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_import_users_filters_csv_and_forces_no_delete_for_domain_admin(
    admin_login_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    import_url = admin_login_url.replace("/login", "/users/import")
    route = respx.post(import_url).mock(return_value=Response(200, json={"created": 1}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/users/import",
        files={
            "csvfile": (
                "users.csv",
                b"username;mail\npatrick;patrick@dev.byrtn.fr\nsomeone;someone@dev.wappos.fr\n",
                "text/csv",
            )
        },
        data={"update": "true", "delete": "true"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 200
    sent_body = route.calls[0].request.content.decode()
    assert "patrick@dev.byrtn.fr" in sent_body
    assert "someone@dev.wappos.fr" not in sent_body
    assert 'name="delete"' not in sent_body
