# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def test_groups_page_shows_owned_domains_section_for_wappos_domain_admins(logged_in_client):
    groups = [
        {"name": "wappos_domain_admins", "members": ["adminbyrtn"], "permissions": [], "is_special": False},
    ]
    with patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}), \
         patch.object(app, "_wappos_api_admin_users", return_value=[]), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr", "dev.wappos.fr"]), \
         patch.object(app, "_wappos_api_all_domain_owners", return_value={"dev.byrtn.fr": ["adminbyrtn"]}):
        resp = logged_in_client.get("/groups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "adminbyrtn" in body
    assert "dev.byrtn.fr" in body
    assert "dev.wappos.fr" in body


def test_update_domain_admin_owned_domains_adds_and_removes(logged_in_client):
    all_owners = {"dev.byrtn.fr": ["adminbyrtn"], "dev.wappos.fr": []}
    with patch.object(app, "_wappos_api_all_domain_owners", return_value=all_owners), \
         patch.object(app, "_wappos_api_set_domain_owners") as mocked_set:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": ["dev.wappos.fr"]},
        )
    assert resp.status_code == 302
    mocked_set.assert_any_call("test-token", "dev.byrtn.fr", [])
    mocked_set.assert_any_call("test-token", "dev.wappos.fr", ["adminbyrtn"])


def test_update_domain_admin_owned_domains_assigns_domain_with_no_prior_registry_entry(logged_in_client):
    with patch.object(app, "_wappos_api_all_domain_owners", return_value={}), \
         patch.object(app, "_wappos_api_set_domain_owners") as mocked_set:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": ["dev.byrtn.fr"]},
        )
    assert resp.status_code == 302
    mocked_set.assert_called_once_with("test-token", "dev.byrtn.fr", ["adminbyrtn"])


def test_update_domain_admin_owned_domains_no_change_calls_nothing(logged_in_client):
    all_owners = {"dev.byrtn.fr": ["adminbyrtn"]}
    with patch.object(app, "_wappos_api_all_domain_owners", return_value=all_owners), \
         patch.object(app, "_wappos_api_set_domain_owners") as mocked_set:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": ["dev.byrtn.fr"]},
        )
    assert resp.status_code == 302
    mocked_set.assert_not_called()


def test_groups_page_shows_primary_domain_selector(logged_in_client):
    groups = [
        {"name": "wappos_domain_admins", "members": ["adminbyrtn"], "permissions": [], "is_special": False},
    ]
    with patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}), \
         patch.object(app, "_wappos_api_admin_users", return_value=[]), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr", "dev.wappos.fr"]), \
         patch.object(app, "_wappos_api_all_domain_owners", return_value={"dev.byrtn.fr": ["adminbyrtn"]}), \
         patch.object(app, "_wappos_api_get_primary_domain", return_value="dev.byrtn.fr"):
        resp = logged_in_client.get("/groups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "is-primary" in body
    assert 'name="primary_domain" value="dev.byrtn.fr"' in body


def test_update_domain_admin_owned_domains_sets_primary_domain(logged_in_client):
    with patch.object(app, "_wappos_api_all_domain_owners", return_value={"dev.byrtn.fr": ["adminbyrtn"]}), \
         patch.object(app, "_wappos_api_set_domain_owners"), \
         patch.object(app, "_wappos_api_set_primary_domain") as mocked_primary:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": ["dev.byrtn.fr"], "primary_domain": "dev.byrtn.fr"},
        )
    assert resp.status_code == 302
    mocked_primary.assert_called_once_with("test-token", "adminbyrtn", "dev.byrtn.fr")


def test_update_domain_admin_owned_domains_leaves_primary_domain_untouched_when_blank(logged_in_client):
    with patch.object(app, "_wappos_api_all_domain_owners", return_value={"dev.byrtn.fr": ["adminbyrtn"]}), \
         patch.object(app, "_wappos_api_set_domain_owners"), \
         patch.object(app, "_wappos_api_set_primary_domain") as mocked_primary:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": ["dev.byrtn.fr"], "primary_domain": ""},
        )
    assert resp.status_code == 302
    mocked_primary.assert_not_called()


def test_update_domain_admin_owned_domains_auto_includes_primary_domain_not_checked(logged_in_client):
    all_owners = {"dev.byrtn.fr": ["adminbyrtn"], "dev.wappos.fr": []}
    with patch.object(app, "_wappos_api_all_domain_owners", return_value=all_owners), \
         patch.object(app, "_wappos_api_set_domain_owners") as mocked_set, \
         patch.object(app, "_wappos_api_set_primary_domain") as mocked_primary:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/owned-domains/adminbyrtn",
            data={"domains": [], "primary_domain": "dev.wappos.fr"},
        )
    assert resp.status_code == 302
    mocked_set.assert_any_call("test-token", "dev.wappos.fr", ["adminbyrtn"])
    mocked_primary.assert_called_once_with("test-token", "adminbyrtn", "dev.wappos.fr")
