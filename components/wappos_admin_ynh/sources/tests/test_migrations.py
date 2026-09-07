# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


def test_migrations_page_requires_authentication(client):
    resp = client.get("/migrations")
    assert resp.status_code == 401


def test_migrations_page_renders_pending_and_done(logged_in_client):
    migrations = [
        {
            "id": "0031_terms_of_services", "number": 31, "name": "terms_of_services",
            "mode": "manual", "state": "pending", "description": "Conditions d'utilisation",
            "disclaimer": "Lisez ceci avant de continuer.",
        },
        {
            "id": "0028_delete_legacy_xmpp_permission", "number": 28, "name": "delete_legacy_xmpp_permission",
            "mode": "auto", "state": "done", "description": "Suppression des anciennes autorisations XMPP",
            "disclaimer": None,
        },
    ]
    with patch.object(app, "_wappos_api_migrations", return_value=migrations):
        resp = logged_in_client.get("/migrations")
    assert resp.status_code == 200
    assert b"Conditions d" in resp.data
    assert b"Lisez ceci avant de continuer" in resp.data
    assert b"Suppression des anciennes autorisations XMPP" in resp.data


def test_migrations_page_api_unreachable_returns_503(logged_in_client):
    with patch.object(app, "_wappos_api_migrations", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.get("/migrations")
    assert resp.status_code == 503


def test_run_migrations_success_redirects_with_message(logged_in_client):
    with patch.object(app, "_wappos_api_run_migrations", return_value={}):
        resp = logged_in_client.post("/migrations/run", data={"target": "0031_terms_of_services", "accept_disclaimer": "1"})
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]


def test_run_migrations_auto_mode_success_redirects_with_message(logged_in_client):
    with patch.object(app, "_wappos_api_run_migrations", return_value={}) as mocked:
        resp = logged_in_client.post("/migrations/run", data={"auto": "1"})
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]
    assert mocked.call_args.kwargs["auto"] is True
    assert mocked.call_args.kwargs["targets"] is None


def test_run_migrations_failure_redirects_with_error(logged_in_client):
    resp_obj = requests.Response()
    resp_obj.status_code = 400
    resp_obj.json = lambda: {"detail": {"code": "migration_failed"}}
    err = requests.exceptions.HTTPError(response=resp_obj)
    with patch.object(app, "_wappos_api_run_migrations", side_effect=err):
        resp = logged_in_client.post("/migrations/run", data={"target": "0031_terms_of_services", "accept_disclaimer": "1"})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]
