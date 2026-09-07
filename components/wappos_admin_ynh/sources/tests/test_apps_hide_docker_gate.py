from unittest.mock import patch

import docker_gate as dg


def test_apps_list_hides_docker_gate_managed_apps(logged_in_client, monkeypatch):
    entry = {"slug": "ghost-container", "yunohost_app_id": "redirect__4"}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])

    raw_apps = [
        {"id": "grav", "name": "Grav", "description": "", "version": "1.0"},
        {"id": "redirect__4", "name": "ghost-container", "description": "", "version": "2.1"},
    ]
    with patch("app._wappos_api_admin_apps", return_value=raw_apps), \
         patch("app._wappos_api_admin_permissions", return_value={}):
        resp = logged_in_client.get("/apps")

    assert resp.status_code == 200
    body = resp.data.decode()
    assert "Grav" in body
    assert "ghost-container" not in body


def test_app_detail_redirects_docker_gate_app_to_docker_apps_page(logged_in_client, monkeypatch):
    entry = {"slug": "ghost-container", "yunohost_app_id": "redirect__4"}
    monkeypatch.setattr(dg, "_load_state", lambda: [entry])

    resp = logged_in_client.get("/apps/redirect__4", follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].startswith("/docker")


def test_app_detail_unaffected_for_non_docker_gate_app(logged_in_client, monkeypatch):
    monkeypatch.setattr(dg, "_load_state", lambda: [])
    detail = {
        "id": "grav", "label": "Grav", "version": "1.0", "description": "", "domain_path": None,
        "logo": None, "is_webapp": False, "supports_change_url": False, "supports_purge": False,
        "notification_post_install": None, "notifications_post_upgrade": {},
        "upgrade": {"status": "up_to_date", "message": "", "current_version": "1.0"},
    }
    with patch("app._wappos_api_app_detail", return_value=detail), \
         patch("app._wappos_api_domains", return_value=[]), \
         patch("app._wappos_api_admin_permissions", return_value={}), \
         patch("app._wappos_api_admin_groups", return_value=[]):
        resp = logged_in_client.get("/apps/grav")

    assert resp.status_code == 200
