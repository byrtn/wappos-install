# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


def _app_detail():
    return {
        "id": "grav", "label": "Grav", "version": "1.0", "description": "", "domain_path": None,
        "logo": None, "is_webapp": False, "supports_change_url": False, "supports_purge": False,
        "notification_post_install": None, "notifications_post_upgrade": {},
        "upgrade": {"status": "up_to_date", "message": "", "current_version": "1.0"},
    }


def _domain_admin_client(client, owned_domains=("dev.byrtn.fr",)):
    with client.session_transaction() as sess:
        sess["user"] = "domain.admin"
        sess["token"] = "test-token"
        sess["is_superadmin"] = False
        sess["owned_domains"] = list(owned_domains)
    return client


def test_domain_detail_works_for_domain_admin_on_owned_domain(client):
    _domain_admin_client(client)
    with patch.object(app, "_wappos_api_domain_detail", return_value={
        "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
        "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
    }), \
         patch.object(app, "_wappos_api_domain_config", return_value={"panels": []}), \
         patch.object(app, "_wappos_api_domain_dns_suggest", return_value=""), \
         patch.object(app, "_wappos_api_settings") as mocked_settings:
        resp = client.get("/domains/dev.byrtn.fr")
    assert resp.status_code == 200
    mocked_settings.assert_not_called()


def test_domain_detail_hides_set_main_domain_for_domain_admin(client):
    _domain_admin_client(client)
    with patch.object(app, "_wappos_api_domain_detail", return_value={
        "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
        "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
    }), \
         patch.object(app, "_wappos_api_domain_config", return_value={"panels": []}), \
         patch.object(app, "_wappos_api_domain_dns_suggest", return_value=""):
        resp = client.get("/domains/dev.byrtn.fr")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert '/domains/dev.byrtn.fr/main' not in body


def test_domain_detail_shows_set_main_domain_for_superadmin(logged_in_client):
    with patch.object(app, "_wappos_api_domain_detail", return_value={
        "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
        "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
    }), \
         patch.object(app, "_wappos_api_domain_config", return_value={"panels": []}), \
         patch.object(app, "_wappos_api_domain_dns_suggest", return_value=""), \
         patch.object(app, "_wappos_api_settings", return_value={"panels": []}):
        resp = logged_in_client.get("/domains/dev.byrtn.fr")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert '/domains/dev.byrtn.fr/main' in body


def test_domain_detail_calls_settings_for_superadmin(logged_in_client):
    with patch.object(app, "_wappos_api_domain_detail", return_value={
        "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
        "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
    }), \
         patch.object(app, "_wappos_api_domain_config", return_value={"panels": []}), \
         patch.object(app, "_wappos_api_domain_dns_suggest", return_value=""), \
         patch.object(app, "_wappos_api_settings", return_value={"panels": []}) as mocked_settings:
        resp = logged_in_client.get("/domains/dev.byrtn.fr")
    assert resp.status_code == 200
    mocked_settings.assert_called_once()


def test_domain_detail_survives_settings_forbidden_for_domain_admin(client):
    _domain_admin_client(client)
    forbidden = requests.exceptions.HTTPError(response=requests.Response())
    with patch.object(app, "_wappos_api_domain_detail", return_value={
        "name": "dev.byrtn.fr", "registrar": None, "main": False, "apps": [],
        "certificate": {"style": "success", "CA_type": "letsencrypt", "validity": 80},
    }), \
         patch.object(app, "_wappos_api_domain_config", return_value={"panels": []}), \
         patch.object(app, "_wappos_api_domain_dns_suggest", return_value=""), \
         patch.object(app, "_wappos_api_settings", side_effect=forbidden):
        resp = client.get("/domains/dev.byrtn.fr")
    assert resp.status_code == 200


def test_app_detail_works_for_domain_admin_when_permissions_succeed_and_groups_forbidden(client, monkeypatch):
    import docker_gate as dg

    _domain_admin_client(client)
    monkeypatch.setattr(dg, "get_app_entry_by_yunohost_id", lambda app_id: None)
    forbidden = requests.exceptions.HTTPError(response=requests.Response())
    with patch.object(app, "_wappos_api_app_detail", return_value=_app_detail()), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={"grav.main": {"label": "grav", "allowed": []}}), \
         patch.object(app, "_wappos_api_admin_groups", side_effect=forbidden):
        resp = client.get("/apps/grav")
    assert resp.status_code == 200


def test_app_detail_survives_groups_forbidden_for_domain_admin(client, monkeypatch):
    import docker_gate as dg

    _domain_admin_client(client)
    monkeypatch.setattr(dg, "get_app_entry_by_yunohost_id", lambda app_id: None)
    forbidden = requests.exceptions.HTTPError(response=requests.Response())
    with patch.object(app, "_wappos_api_app_detail", return_value=_app_detail()), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
         patch.object(app, "_wappos_api_admin_permissions", side_effect=forbidden), \
         patch.object(app, "_wappos_api_admin_groups", side_effect=forbidden):
        resp = client.get("/apps/grav")
    assert resp.status_code == 200
