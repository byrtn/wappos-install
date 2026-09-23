# Auteur : Patrick Ritaine
from unittest.mock import patch

import app


def test_wappos_domain_admins_group_has_no_delete_button(logged_in_client):
    groups = [
        {"name": "admins", "members": ["adminynh"], "permissions": [], "is_special": True},
        {"name": "wappos_domain_admins", "members": [], "permissions": [], "is_special": False},
        {"name": "team", "members": [], "permissions": [], "is_special": False},
    ]
    with patch.object(app, "_wappos_api_admin_groups", return_value=groups), \
         patch.object(app, "_wappos_api_admin_permissions", return_value={}), \
         patch.object(app, "_wappos_api_admin_users", return_value=[]):
        resp = logged_in_client.get("/groups")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert '/groups/wappos_domain_admins/delete' not in body
    assert '/groups/team/delete' in body
