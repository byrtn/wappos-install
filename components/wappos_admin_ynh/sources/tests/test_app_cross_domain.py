# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def _app_detail(is_webapp=True):
    return {
        "id": "grav", "label": "Grav", "version": "1.0", "description": "", "domain_path": "dev.byrtn.fr/actus",
        "logo": None, "is_webapp": is_webapp, "supports_change_url": True, "supports_purge": False,
        "notification_post_install": None, "notifications_post_upgrade": {},
        "upgrade": {"status": "up_to_date", "message": "", "current_version": "1.0"},
    }


def test_app_detail_shows_cross_domain_section_for_webapp(logged_in_client):
    with patch.object(app, "_wappos_api_app_detail", return_value=_app_detail()), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr", "dev.wappos.fr"]), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}), \
         patch.object(app, "_wappos_api_admin_groups", return_value=[]), \
         patch.object(app, "_wappos_api_cross_domain_list", return_value=["dev.wappos.fr"]):
        resp = logged_in_client.get("/apps/grav")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "dev.wappos.fr" in body
    assert "/apps/grav/cross-domain/add" in body
    assert "/apps/grav/cross-domain/remove" in body


def test_app_cross_domain_add_requires_domain(logged_in_client):
    resp = logged_in_client.post("/apps/grav/cross-domain/add", data={"domain": ""})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_app_cross_domain_add_calls_api(logged_in_client):
    with patch.object(app, "_wappos_api_cross_domain_add") as add_mock:
        resp = logged_in_client.post("/apps/grav/cross-domain/add", data={"domain": "dev.wappos.fr"})
    assert resp.status_code == 302
    add_mock.assert_called_once_with("test-token", "grav", "dev.wappos.fr")


def test_app_cross_domain_remove_calls_api(logged_in_client):
    with patch.object(app, "_wappos_api_cross_domain_remove") as remove_mock:
        resp = logged_in_client.post("/apps/grav/cross-domain/remove", data={"domain": "dev.wappos.fr"})
    assert resp.status_code == 302
    remove_mock.assert_called_once_with("test-token", "grav", "dev.wappos.fr")
