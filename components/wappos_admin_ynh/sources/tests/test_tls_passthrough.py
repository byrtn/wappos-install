# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def _domain_admin_client(client, monkeypatch=None):
    with client.session_transaction() as sess:
        sess["user"] = "domain.admin"
        sess["token"] = "test-token"
        sess["is_superadmin"] = False
        sess["owned_domains"] = ["dev.byrtn.fr"]
    if monkeypatch is not None:
        monkeypatch.setattr(
            app, "_wappos_api_admin_session",
            lambda token: {"is_superadmin": False, "owned_domains": ["dev.byrtn.fr"]},
        )
    return client


def test_tls_passthrough_page_renders_entries_for_superadmin(logged_in_client):
    data = {"enabled": True, "entries": [{"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": 443}]}
    with patch.object(app, "_wappos_api_tls_passthrough", return_value=data):
        resp = logged_in_client.get("/tls-passthrough")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "dev.byrtn.fr" in body
    assert "192.168.1.42:443" in body


def test_tls_passthrough_page_shows_free_text_domain_for_superadmin(logged_in_client):
    data = {"enabled": False, "entries": []}
    with patch.object(app, "_wappos_api_tls_passthrough", return_value=data):
        resp = logged_in_client.get("/tls-passthrough")
    body = resp.data.decode()
    assert '<input type="text" id="tp-domain" name="domain"' in body


def test_tls_passthrough_page_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/tls-passthrough")
    assert resp.status_code == 403


def test_add_tls_passthrough_entry_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.post(
        "/tls-passthrough/add",
        data={"domain": "dev.byrtn.fr", "destination": "127.0.0.1", "port": "443"},
    )
    assert resp.status_code == 403


def test_remove_tls_passthrough_entry_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.post(
        "/tls-passthrough/remove",
        data={"domain": "dev.byrtn.fr", "destination": "127.0.0.1", "port": "443"},
    )
    assert resp.status_code == 403


def test_add_tls_passthrough_entry_appends_and_redirects(logged_in_client):
    existing = {"enabled": False, "entries": []}
    with patch.object(app, "_wappos_api_tls_passthrough", return_value=existing), \
         patch.object(app, "_wappos_api_update_tls_passthrough") as update_mock:
        resp = logged_in_client.post(
            "/tls-passthrough/add",
            data={"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": "443"},
        )
    assert resp.status_code == 302
    update_mock.assert_called_once_with(
        "test-token", [{"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": 443}]
    )


def test_add_tls_passthrough_entry_requires_all_fields(logged_in_client):
    resp = logged_in_client.post("/tls-passthrough/add", data={"domain": "dev.byrtn.fr", "destination": "", "port": ""})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_remove_tls_passthrough_entry_filters_and_redirects(logged_in_client):
    existing = {
        "enabled": True,
        "entries": [
            {"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": 443},
            {"domain": "dev.wappos.fr", "destination": "10.0.0.5", "port": 8443},
        ],
    }
    with patch.object(app, "_wappos_api_tls_passthrough", return_value=existing), \
         patch.object(app, "_wappos_api_update_tls_passthrough") as update_mock:
        resp = logged_in_client.post(
            "/tls-passthrough/remove",
            data={"domain": "dev.byrtn.fr", "destination": "192.168.1.42", "port": "443"},
        )
    assert resp.status_code == 302
    update_mock.assert_called_once_with(
        "test-token", [{"domain": "dev.wappos.fr", "destination": "10.0.0.5", "port": 8443}]
    )
