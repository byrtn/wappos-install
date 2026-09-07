# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app
import docker_gate as dg


def _entry():
    return {
        "slug": "grafana", "yunohost_app_id": "redirect__3",
        "image": "grafana/grafana", "container_port": "3000",
        "data_path": "/var/lib/grafana", "cpu_limit": "", "mem_limit": "",
        "domain": "dev.byrtn.fr", "path": "/grafana",
    }


def test_docker_edit_shows_access_and_tile_cards(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    permissions = {"redirect__3.main": {"label": "grafana", "allowed": ["all_users"], "show_tile": True, "hide_from_public": False, "protected": False, "order": None, "description": ""}}
    groups = [{"name": "all_users"}, {"name": "visitors"}]
    with patch("app._wappos_api_admin_permissions", return_value=permissions), \
         patch("app._wappos_api_admin_groups", return_value=groups):
        resp = logged_in_client.get("/docker/edit/grafana")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "Accès" in body
    assert "Afficher la tuile dans le portail" in body
    assert 'action="/permissions/redirect__3.main/groups"' in body
    assert 'action="/permissions/redirect__3.main/properties"' in body


def test_update_permission_groups_redirects_to_docker_edit_for_docker_gate_app(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "grafana", "yunohost_app_id": "redirect__3"}])
    with patch("app._wappos_api_admin_permissions", return_value={"redirect__3.main": {"allowed": []}}), \
         patch("app._wappos_api_update_permission", return_value=None):
        resp = logged_in_client.post("/permissions/redirect__3.main/groups", data={"groups": ["all_users"]}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/docker/edit/grafana" in resp.headers["Location"]


def test_update_permission_groups_redirects_to_app_detail_for_native_app(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with patch("app._wappos_api_admin_permissions", return_value={"grav.main": {"allowed": []}}), \
         patch("app._wappos_api_update_permission", return_value=None):
        resp = logged_in_client.post("/permissions/grav.main/groups", data={"groups": ["all_users"]}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/apps/grav" in resp.headers["Location"]


def test_update_permission_properties_redirects_to_docker_edit_for_docker_gate_app(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "grafana", "yunohost_app_id": "redirect__3"}])
    with patch("app._wappos_api_update_permission_properties", return_value=None), \
         patch("app._wappos_api_admin_permissions", return_value={"redirect__3.main": {"show_tile": True}}):
        resp = logged_in_client.post("/permissions/redirect__3.main/properties", data={"label": "Grafana", "show_tile": "on"}, follow_redirects=False)
    assert resp.status_code == 302
    assert "/docker/edit/grafana" in resp.headers["Location"]


def test_update_permission_properties_redirects_to_apps_for_native_app(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    with patch("app._wappos_api_update_permission_properties", return_value=None), \
         patch("app._wappos_api_admin_permissions", return_value={"grav.main": {"show_tile": True}}):
        resp = logged_in_client.post("/permissions/grav.main/properties", data={"label": "Grav", "show_tile": "on"}, follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/apps") or "/apps?" in resp.headers["Location"]


def test_update_permission_properties_omits_empty_label_and_description(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [{"slug": "grafana", "yunohost_app_id": "redirect__3"}])
    captured = {}

    def _fake_update(token, permission, **fields):
        captured.update(fields)

    with patch("app._wappos_api_update_permission_properties", side_effect=_fake_update), \
         patch("app._wappos_api_admin_permissions", return_value={"redirect__3.main": {"show_tile": True}}):
        resp = logged_in_client.post(
            "/permissions/redirect__3.main/properties",
            data={"label": "", "description": "", "order": ""},
            follow_redirects=False,
        )
    assert resp.status_code == 302
    assert captured["label"] is None
    assert captured["description"] is None
    assert captured["order"] is None


def test_docker_edit_shows_change_url_card_when_supported(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    with patch("app._wappos_api_admin_permissions", return_value={}), \
         patch("app._wappos_api_admin_groups", return_value=[]), \
         patch("app._wappos_api_app_detail", return_value={"supports_change_url": True}), \
         patch("app._wappos_api_domains", return_value=["dev.byrtn.fr", "byrtn.fr"]):
        resp = logged_in_client.get("/docker/edit/grafana")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "Changer l'URL" in body
    assert "dev.byrtn.fr/grafana" in body


def test_docker_edit_hides_change_url_card_when_unsupported(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    with patch("app._wappos_api_admin_permissions", return_value={}), \
         patch("app._wappos_api_admin_groups", return_value=[]), \
         patch("app._wappos_api_app_detail", return_value={"supports_change_url": False}), \
         patch("app._wappos_api_domains", return_value=["dev.byrtn.fr"]):
        resp = logged_in_client.get("/docker/edit/grafana")
    assert "Changer l'URL" not in resp.data.decode()


def test_docker_change_url_success_updates_docker_gate_state_and_redirects(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    captured = {}
    monkeypatch.setattr(dg, "update_docker_app_url", lambda slug, domain, path: captured.update(slug=slug, domain=domain, path=path))
    with patch("app._wappos_api_change_app_url", return_value=None) as mocked:
        resp = logged_in_client.post(
            "/docker/change_url/grafana", data={"domain": "byrtn.fr", "path": "monitoring"}, follow_redirects=False,
        )
    assert resp.status_code == 302
    assert "/docker/edit/grafana" in resp.headers["Location"]
    mocked.assert_called_once()
    assert captured == {"slug": "grafana", "domain": "byrtn.fr", "path": "/monitoring"}


def test_docker_change_url_api_failure_does_not_update_docker_gate_state(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    called = []
    monkeypatch.setattr(dg, "update_docker_app_url", lambda *a, **k: called.append(True))
    with patch("app._wappos_api_change_app_url", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.post(
            "/docker/change_url/grafana", data={"domain": "byrtn.fr", "path": "/monitoring"}, follow_redirects=False,
        )
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]
    assert called == []


def test_docker_change_url_requires_domain_and_path(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    resp = logged_in_client.post("/docker/change_url/grafana", data={"domain": "", "path": ""}, follow_redirects=False)
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_docker_edit_survives_expired_token_on_permissions_lookup(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "get_app_entry", lambda slug: _entry())
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    with patch("app._wappos_api_admin_permissions", side_effect=app.SessionExpiredError()), \
         patch("app._wappos_api_app_detail", side_effect=app.SessionExpiredError()):
        resp = logged_in_client.get("/docker/edit/grafana")
    assert resp.status_code == 200
    with logged_in_client.session_transaction() as sess:
        assert sess.get("user") == "adminynh"
