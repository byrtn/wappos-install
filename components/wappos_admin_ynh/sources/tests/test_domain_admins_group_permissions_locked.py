# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def test_update_group_permissions_rejected_for_wappos_domain_admins(logged_in_client):
    with patch.object(app, "_wappos_api_update_permission") as mocked_update:
        resp = logged_in_client.post(
            "/groups/wappos_domain_admins/permissions",
            data={"permissions": ["ssh.main"]},
        )
    assert resp.status_code == 302
    mocked_update.assert_not_called()


def test_update_group_permissions_still_works_for_other_groups(logged_in_client):
    groups = [{"name": "team", "members": [], "permissions": [], "is_special": False}]
    with patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_update_permission") as mocked_update:
        resp = logged_in_client.post(
            "/groups/team/permissions",
            data={"permissions": ["nextcloud.main"]},
        )
    assert resp.status_code == 302
    mocked_update.assert_called_once_with("test-token", "nextcloud.main", add=["team"])


def test_groups_page_hides_permission_checklist_for_wappos_domain_admins(logged_in_client):
    groups = [
        {"name": "wappos_domain_admins", "members": ["adminbyrtn"], "permissions": [], "is_special": False},
    ]
    permission_options = [
        {"id": "ssh.main", "label": "SSH", "protected": True, "url": None, "additional_urls": [], "corresponding_users": []},
    ]
    with patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={p["id"]: p for p in permission_options}), \
         patch.object(app, "_wappos_api_admin_users", return_value=[]), \
         patch.object(app, "_wappos_api_domains", return_value=[]), \
         patch.object(app, "_wappos_api_all_domain_owners", return_value={}):
        resp = logged_in_client.get("/groups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'action="/groups/wappos_domain_admins/permissions"' not in body
