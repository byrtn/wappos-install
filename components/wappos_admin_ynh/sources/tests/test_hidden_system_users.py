# Auteur : Patrick Ritaine
from unittest.mock import MagicMock, patch

import app


def _fake_response(json_data, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def test_admin_users_hides_wappos_svc_admin():
    raw_users = [
        {"username": "patrick.ritaine", "fullname": "Patrick", "mail": "patrick@dev.byrtn.fr"},
        {"username": "wappos_svc_admin", "fullname": "Wappos API", "mail": "wappos_svc_admin@dev.byrtn.fr"},
        {"username": "cron.alerts", "fullname": "SYSTEME", "mail": "cron.alerts@dev.byrtn.fr"},
    ]
    with patch.object(app.requests, "get", return_value=_fake_response(raw_users)):
        users = app._wappos_api_admin_users("test-token")
    usernames = {u["username"] for u in users}
    assert usernames == {"patrick.ritaine"}


def test_admin_groups_hides_wappos_svc_admin_personal_group():
    raw_groups = [
        {"name": "admins", "members": ["patrick.ritaine", "wappos_svc_admin"], "permissions": []},
        {"name": "wappos_svc_admin", "members": ["wappos_svc_admin"], "permissions": []},
        {"name": "wappos_domain_admins", "members": [], "permissions": []},
    ]
    with patch.object(app.requests, "get", return_value=_fake_response(raw_groups)):
        groups = app._wappos_api_admin_groups("test-token")
    group_names = {g["name"] for g in groups}
    assert group_names == {"admins", "wappos_domain_admins"}
