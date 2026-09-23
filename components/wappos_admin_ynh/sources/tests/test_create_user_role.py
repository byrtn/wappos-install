# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def _domain_admin_client(client, owned_domains=("dev.byrtn.fr",)):
    with client.session_transaction() as sess:
        sess["user"] = "domain.admin"
        sess["token"] = "test-token"
        sess["is_superadmin"] = False
        sess["owned_domains"] = list(owned_domains)
    return client


def test_create_user_without_role_does_not_call_group_update(logged_in_client):
    with patch.object(app, "_wappos_api_create_user") as create_mock, \
         patch.object(app, "_wappos_api_update_group_members") as group_mock:
        resp = logged_in_client.post(
            "/users",
            data={
                "username": "newuser", "domain": "dev.byrtn.fr", "fullname": "New User",
                "new_password": "longenough1", "new_password_confirm": "longenough1",
            },
        )
    assert resp.status_code == 302
    assert create_mock.called
    group_mock.assert_not_called()


def test_create_user_with_role_assigns_group(logged_in_client):
    with patch.object(app, "_wappos_api_create_user"), \
         patch.object(app, "_wappos_api_update_group_members") as group_mock:
        resp = logged_in_client.post(
            "/users",
            data={
                "username": "newuser", "domain": "dev.byrtn.fr", "fullname": "New User",
                "new_password": "longenough1", "new_password_confirm": "longenough1",
                "role": "admins",
            },
        )
    assert resp.status_code == 302
    group_mock.assert_called_once_with("test-token", "admins", add=["newuser"])


def test_create_user_domain_admin_role_shows_next_step_message(logged_in_client):
    with patch.object(app, "_wappos_api_create_user"), \
         patch.object(app, "_wappos_api_update_group_members"):
        resp = logged_in_client.post(
            "/users",
            data={
                "username": "newuser", "domain": "dev.byrtn.fr", "fullname": "New User",
                "new_password": "longenough1", "new_password_confirm": "longenough1",
                "role": "wappos_domain_admins",
            },
        )
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]


def test_create_user_role_assignment_failure_reports_but_user_already_created(logged_in_client):
    import requests

    error_resp = requests.Response()
    error_resp.status_code = 403
    http_error = requests.exceptions.HTTPError(response=error_resp)

    with patch.object(app, "_wappos_api_create_user"), \
         patch.object(app, "_wappos_api_update_group_members", side_effect=http_error):
        resp = logged_in_client.post(
            "/users",
            data={
                "username": "newuser", "domain": "dev.byrtn.fr", "fullname": "New User",
                "new_password": "longenough1", "new_password_confirm": "longenough1",
                "role": "admins",
            },
        )
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_users_page_hides_superadmin_and_domain_admin_role_options_for_domain_admin(client):
    _domain_admin_client(client)
    groups = [{"name": "team", "members": []}]
    with patch.object(app, "_wappos_api_admin_users", return_value=[]), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
         patch.object(app, "_wappos_api_admin_groups", return_value=groups):
        resp = client.get("/users")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'value="admins"' not in body
    assert 'value="wappos_domain_admins"' not in body
    assert 'value="team"' in body


def test_users_page_shows_all_role_options_for_superadmin(logged_in_client):
    groups = [
        {"name": "admins", "members": []},
        {"name": "wappos_domain_admins", "members": []},
        {"name": "team", "members": []},
    ]
    with patch.object(app, "_wappos_api_admin_users", return_value=[]), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
         patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_all_domain_owners", return_value={}):
        resp = logged_in_client.get("/users")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'value="admins"' in body
    assert 'value="wappos_domain_admins"' in body
    assert 'value="visitors"' in body
    assert 'value="team"' in body
