# Auteur : Patrick Ritaine
from unittest.mock import patch

import app

_USERS = [
    {"username": "zzz.user", "fullname": "ZZZ User", "mail": "zzz.user@dev.byrtn.fr"},
    {"username": "adminynh", "fullname": "Admin YNH", "mail": "adminynh@dev.byrtn.fr"},
    {"username": "domain.admin", "fullname": "Domain Admin", "mail": "domain.admin@dev.byrtn.fr"},
]

_GROUPS = [
    {"name": "admins", "members": ["adminynh"], "permissions": [], "is_special": True},
    {"name": "wappos_domain_admins", "members": ["domain.admin"], "permissions": [], "is_special": False},
]


def test_user_list_shows_role_badges_and_sorts_by_role(logged_in_client):
    with patch.object(app, "_wappos_api_admin_users", return_value=list(_USERS)), \
         patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
         patch.object(app, "_wappos_api_admin_groups", return_value=_GROUPS), \
         patch.object(app, "_wappos_api_all_domain_owners", return_value={"dev.byrtn.fr": ["domain.admin"]}):
        resp = logged_in_client.get("/users")

    body = resp.data.decode()
    assert resp.status_code == 200
    assert "Superadmin" in body
    assert "dev.byrtn.fr" in body
    assert body.index("adminynh") < body.index("domain.admin") < body.index("zzz.user")


def test_user_list_shows_no_domain_assigned_for_domain_admin_without_domain():
    flask_app = app.app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = "adminynh"
            sess["token"] = "test-token"
            sess["is_superadmin"] = True
        with patch.object(app, "_wappos_api_admin_users", return_value=[_USERS[2]]), \
             patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
             patch.object(app, "_wappos_api_admin_groups", return_value=_GROUPS), \
             patch.object(app, "_wappos_api_all_domain_owners", return_value={}):
            resp = client.get("/users")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "aucun domaine attribu" in body or "no domain assigned" in body


def test_user_list_hides_role_badges_for_domain_admin_viewer():
    flask_app = app.app
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user"] = "domain.admin"
            sess["token"] = "test-token"
            sess["is_superadmin"] = False
            sess["owned_domains"] = ["dev.byrtn.fr"]
        with patch.object(app, "_wappos_api_admin_users", return_value=[_USERS[0]]), \
             patch.object(app, "_wappos_api_domains", return_value=["dev.byrtn.fr"]), \
             patch.object(app, "_wappos_api_admin_groups", return_value=[]):
            resp = client.get("/users")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert 'value="admins"' not in body
    assert 'value="wappos_domain_admins"' not in body
