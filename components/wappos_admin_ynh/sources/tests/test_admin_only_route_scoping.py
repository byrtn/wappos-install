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


def test_backups_page_allowed_and_hides_schedule_for_domain_admin(client):
    _domain_admin_client(client)
    with patch.object(app, "_wappos_api_list_backups", return_value={"archives": {}}), \
         patch.object(app, "_wappos_api_admin_apps", return_value=[]):
        resp = client.get("/backups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/backups/schedule" not in body


def test_backups_page_shows_schedule_for_superadmin(logged_in_client):
    with patch.object(app, "_wappos_api_list_backups", return_value={"archives": {}}), \
         patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(app, "_wappos_api_settings", return_value={"panels": []}):
        resp = logged_in_client.get("/backups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/backups/schedule" in body


def test_save_backup_schedule_forbidden_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    resp = client.post("/backups/schedule", data={"enabled": "1", "frequency": "daily", "scope": "full"})
    assert resp.status_code == 403


def test_preview_backup_retention_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/backups/retention/preview")
    assert resp.status_code == 403


def test_failed_units_page_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/failed-units")
    assert resp.status_code == 403


def test_performance_page_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/performance")
    assert resp.status_code == 403


def test_save_backup_schedule_uses_live_scope_not_stale_session(client):
    _domain_admin_client(client)
    with client.session_transaction() as sess:
        sess["is_superadmin"] = False
    with patch.object(app, "_wappos_api_admin_session", return_value={"is_superadmin": True, "owned_domains": []}):
        resp = client.post("/backups/schedule", data={"enabled": "1", "frequency": "daily", "scope": "full"})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["is_superadmin"] is True


def test_app_catalog_allowed_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    with patch.object(app, "_wappos_api_app_catalog", return_value={"apps": [], "categories": [], "antifeatures": []}):
        resp = client.get("/apps/catalog")
    assert resp.status_code == 200


def test_app_install_form_forbidden_without_domain_arg_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    manifest = {"id": "some_tool", "name": "Some Tool", "install": []}
    with patch.object(app, "_wappos_api_app_manifest", return_value=manifest):
        resp = client.get("/apps/install/some_tool")
    assert resp.status_code == 403


def test_app_install_form_filters_domain_choices_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    manifest = {
        "id": "grav", "name": "Grav", "install": [
            {"id": "domain", "choices": {"dev.byrtn.fr": "dev.byrtn.fr", "dev.wappos.fr": "dev.wappos.fr"}},
        ],
        "upstream": {}, "requirements": {},
    }
    with patch.object(app, "_wappos_api_app_manifest", return_value=manifest), \
         patch.object(app, "_wappos_api_app_catalog", return_value={"apps": [], "antifeatures": []}):
        resp = client.get("/apps/install/grav")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "dev.byrtn.fr" in body
    assert "dev.wappos.fr" not in body


def test_app_install_submit_forces_off_all_domains_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    manifest = {"id": "grav", "name": "Grav", "install": [{"id": "domain"}]}
    with patch.object(app, "_wappos_api_app_manifest", return_value=manifest), \
         patch.object(app, "_wappos_api_install_app") as install_mock, \
         patch.object(app, "_wappos_api_set_cross_domain") as cross_domain_mock:
        resp = client.post(
            "/apps/install/grav",
            data={"label": "Grav", "domain": "dev.byrtn.fr", "path": "/actus", "all_domains": "on"},
        )
    assert resp.status_code == 302
    assert install_mock.called
    cross_domain_mock.assert_not_called()


def test_app_install_custom_forbidden_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, monkeypatch)
    resp = client.post("/apps/install-custom", data={"url": "https://example.com/app"})
    assert resp.status_code == 403


def test_save_backup_schedule_revoked_superadmin_blocked_despite_stale_cached_session(logged_in_client):
    with patch.object(app, "_wappos_api_admin_session", return_value={"is_superadmin": False, "owned_domains": []}):
        resp = logged_in_client.post("/backups/schedule", data={"enabled": "1", "frequency": "daily", "scope": "full"})
    assert resp.status_code == 403


def test_apps_page_shows_install_link_for_domain_admin(client):
    _domain_admin_client(client)
    with patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}):
        resp = client.get("/apps")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/apps/catalog" in body


def test_apps_page_shows_install_link_for_superadmin(logged_in_client):
    with patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}):
        resp = logged_in_client.get("/apps")
    assert "/apps/catalog" in resp.data.decode()


def test_home_page_shows_install_app_quick_link_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/apps/catalog" in body


def test_home_page_shows_install_app_quick_link_for_superadmin(logged_in_client):
    empty_summary = {
        "mounts": None, "services_down": None, "services_total": None,
        "diag_errors": None, "diag_warnings": None, "last_backup": None,
        "app_updates": None, "system_update_categories": None, "failed_units": None,
    }
    with patch.object(app, "_dashboard_summary", return_value=empty_summary):
        resp = logged_in_client.get("/")
    assert "/apps/catalog" in resp.data.decode()


def test_home_page_shows_groups_and_system_links_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/groups" in body
    assert "/system-menu" in body
    assert "/diagnosis" in body
    assert "/backups" in body


def test_system_menu_page_shows_only_firewall_and_logs_for_domain_admin(client):
    _domain_admin_client(client)
    resp = client.get("/system-menu")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'href="/firewall"' in body
    assert 'href="/logs"' in body
    assert 'href="/tls-passthrough"' not in body
    assert 'href="/settings"' not in body
    assert 'href="/system"' not in body
    assert 'href="/migrations"' not in body
    assert 'href="/security"' not in body
    assert 'href="/services"' not in body
    assert 'href="/performance"' not in body
    assert 'href="/storage"' not in body
    assert 'href="/app-map"' not in body


def test_system_menu_page_shows_all_links_for_superadmin(logged_in_client):
    resp = logged_in_client.get("/system-menu")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'href="/firewall"' in body
    assert 'href="/tls-passthrough"' in body
    assert 'href="/settings"' in body
    assert 'href="/migrations"' in body


def test_firewall_page_hides_upnp_controls_for_domain_admin(client):
    _domain_admin_client(client)
    empty_rules = {"tcp": [], "udp": [], "upnp_enabled": False}
    with patch.object(app, "_wappos_api_firewall", return_value=empty_rules):
        resp = client.get("/firewall")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'id="op-upnp"' not in body
    assert "/firewall/upnp/" not in body


def test_firewall_page_shows_upnp_controls_for_superadmin(logged_in_client):
    empty_rules = {"tcp": [], "udp": [], "upnp_enabled": False}
    with patch.object(app, "_wappos_api_firewall", return_value=empty_rules):
        resp = logged_in_client.get("/firewall")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'id="op-upnp"' in body
    assert "/firewall/upnp/" in body


def test_diagnosis_page_hides_full_run_button_for_domain_admin(client):
    _domain_admin_client(client)
    with patch.object(app, "_wappos_api_admin_diagnosis", return_value=[]), \
         patch.object(app, "_wappos_api_diagnosis_categories", return_value=["dnsrecords", "web"]):
        resp = client.get("/diagnosis")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'id="diag-run-full-form"' not in body
    assert '<select name="category"' in body


def test_diagnosis_page_shows_full_run_button_for_superadmin(logged_in_client):
    with patch.object(app, "_wappos_api_admin_diagnosis", return_value=[]), \
         patch.object(app, "_wappos_api_diagnosis_categories", return_value=["dnsrecords", "web", "mail"]):
        resp = logged_in_client.get("/diagnosis")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'id="diag-run-full-form"' in body


def test_log_detail_page_hides_share_button_for_domain_admin(client):
    _domain_admin_client(client)
    detail = {"name": "domain_cert_install-dev.byrtn.fr", "description": "x", "logs": [], "suboperations": []}
    with patch.object(app, "_wappos_api_log_detail", return_value=detail):
        resp = client.get("/logs/domain_cert_install-dev.byrtn.fr")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/logs/domain_cert_install-dev.byrtn.fr/share" not in body


def test_log_detail_page_shows_share_button_for_superadmin(logged_in_client):
    detail = {"name": "op1", "description": "x", "logs": [], "suboperations": []}
    with patch.object(app, "_wappos_api_log_detail", return_value=detail):
        resp = logged_in_client.get("/logs/op1")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "/logs/op1/share" in body
