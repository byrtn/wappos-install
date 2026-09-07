# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


def test_unauthenticated_get_returns_login_page_401(client):
    resp = client.get("/domains")
    assert resp.status_code == 401
    assert b"login" in resp.data.lower() or resp.request.path == "/domains"


def test_static_files_bypass_login_gate(client):
    resp = client.get("/static/docker-gate-app-logo.png")
    assert resp.status_code == 200


def test_login_success_sets_session_and_redirects(client):
    with patch.object(app, "_wappos_api_admin_login", return_value="tok123"):
        resp = client.post("/login", data={"username": "adminynh", "password": "secret"})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user"] == "adminynh"
        assert sess["token"] == "tok123"


def test_login_invalid_credentials_returns_401(client):
    err = requests.exceptions.HTTPError(response=requests.Response())
    with patch.object(app, "_wappos_api_admin_login", side_effect=err):
        resp = client.post("/login", data={"username": "adminynh", "password": "wrong"})
    assert resp.status_code == 401


def test_login_api_unreachable_returns_503(client):
    with patch.object(app, "_wappos_api_admin_login", side_effect=requests.exceptions.ConnectionError()):
        resp = client.post("/login", data={"username": "adminynh", "password": "secret"})
    assert resp.status_code == 503


def test_logout_clears_session(logged_in_client):
    resp = logged_in_client.post("/logout")
    assert resp.status_code == 302
    with logged_in_client.session_transaction() as sess:
        assert "user" not in sess


def test_session_expired_error_clears_session_and_returns_401():
    flask_app = app.app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user"] = "adminynh"
            sess["token"] = "expired-token"
        with patch.object(app, "_wappos_api_app_map", side_effect=app.SessionExpiredError()):
            resp = c.get("/app-map")
        assert resp.status_code == 401
        with c.session_transaction() as sess:
            assert "user" not in sess


def test_unknown_route_returns_404_for_authenticated_user(logged_in_client):
    resp = logged_in_client.get("/this-route-does-not-exist")
    assert resp.status_code == 404


def test_unknown_route_returns_login_page_for_anonymous_user(client):
    resp = client.get("/this-route-does-not-exist")
    assert resp.status_code == 401
