# Auteur : Patrick Ritaine
import base64
from unittest.mock import patch

import pytest
import requests

import app


def _b64(url: str) -> str:
    return base64.b64encode(url.encode("utf-8")).decode("ascii")


@pytest.fixture(autouse=True)
def _reset_branding_cache():
    app._branding_cache["value"] = None
    app._branding_cache["fetched_at"] = 0.0
    yield


@pytest.fixture(autouse=True)
def _no_public_settings_by_default():
    with patch.object(app, "_public_settings_safe", return_value={}):
        yield


def test_index_anonymous_shows_login_page(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower() or resp.request.path == "/"


def test_index_anonymous_with_r_shows_protected_message(client):
    resp = client.get("/", query_string={"r": _b64("https://adguard.byrtn.fr/")})
    assert resp.status_code == 200
    assert "connecte-toi".encode() in resp.data.lower() or "log in".encode() in resp.data.lower()


def test_index_anonymous_without_r_shows_no_protected_message(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"connecte-toi pour" not in resp.data.lower()


def test_index_authenticated_lists_tiles(logged_in_client):
    me = {"mail": "patrick@byrtn.fr", "groups": ["all_users"], "apps": {
        "grav.main": {"label": "Grav", "url": "https://byrtn.fr/"},
    }}
    with patch.object(app, "_wappos_api_me", return_value=me):
        resp = logged_in_client.get("/")
    assert resp.status_code == 200


def test_index_authenticated_with_access_denied_shows_error_and_tiles(logged_in_client):
    me = {"mail": "patrick@byrtn.fr", "groups": ["all_users"], "apps": {
        "grav.main": {"label": "Grav", "url": "https://byrtn.fr/"},
    }}
    with patch.object(app, "_wappos_api_me", return_value=me):
        resp = logged_in_client.get("/", query_string={"msg": "access_denied"})
    assert resp.status_code == 200
    assert b"permission" in resp.data.lower()
    assert b"grav" in resp.data.lower()


def test_index_authenticated_api_unreachable_returns_503(logged_in_client):
    with patch.object(app, "_wappos_api_me", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.get("/")
    assert resp.status_code == 503


def test_login_success_sets_session_and_redirects(client):
    with patch.object(app, "_wappos_api_login", return_value=("tok123", None)):
        resp = client.post("/login", data={"username": "patrick", "password": "secret"})
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["user"] == "patrick"
        assert sess["token"] == "tok123"


def test_login_invalid_credentials_returns_401(client):
    err = requests.exceptions.HTTPError(response=requests.Response())
    with patch.object(app, "_wappos_api_login", side_effect=err):
        resp = client.post("/login", data={"username": "patrick", "password": "wrong"})
    assert resp.status_code == 401


def test_login_api_unreachable_returns_503(client):
    with patch.object(app, "_wappos_api_login", side_effect=requests.exceptions.ConnectionError()):
        resp = client.post("/login", data={"username": "patrick", "password": "secret"})
    assert resp.status_code == 503


def test_login_redirects_to_safe_next_path(client):
    with patch.object(app, "_wappos_api_login", return_value=("tok123", None)):
        resp = client.post("/login", data={"username": "patrick", "password": "secret", "next": "/support"})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/support"


def test_login_ignores_unsafe_next_path(client):
    with patch.object(app, "_wappos_api_login", return_value=("tok123", None)):
        resp = client.post("/login", data={"username": "patrick", "password": "secret", "next": "//evil.example.com"})
    assert resp.status_code == 302
    assert resp.headers["Location"] != "//evil.example.com"


def test_index_authenticated_with_valid_r_redirects_onward(logged_in_client):
    with patch.object(app, "_known_domain_names", return_value={"adguard.byrtn.fr"}):
        resp = logged_in_client.get("/", query_string={"r": _b64("https://adguard.byrtn.fr/")})
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://adguard.byrtn.fr/"


def test_index_authenticated_with_unknown_r_shows_portal(logged_in_client):
    me = {"mail": "patrick@byrtn.fr", "groups": ["all_users"], "apps": {}}
    with patch.object(app, "_known_domain_names", return_value=set()), \
         patch.object(app, "_wappos_api_me", return_value=me):
        resp = logged_in_client.get("/", query_string={"r": _b64("https://evil.example.com/")})
    assert resp.status_code == 200


def test_login_redirects_to_r_target_when_no_next(client):
    with patch.object(app, "_wappos_api_login", return_value=("tok123", None)), \
         patch.object(app, "_known_domain_names", return_value={"adguard.byrtn.fr"}):
        resp = client.post(
            "/login",
            data={"username": "patrick", "password": "secret", "r": _b64("https://adguard.byrtn.fr/")},
        )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "https://adguard.byrtn.fr/"


def test_login_next_takes_priority_over_r(client):
    with patch.object(app, "_wappos_api_login", return_value=("tok123", None)), \
         patch.object(app, "_known_domain_names", return_value={"adguard.byrtn.fr"}):
        resp = client.post(
            "/login",
            data={
                "username": "patrick", "password": "secret",
                "next": "/support", "r": _b64("https://adguard.byrtn.fr/"),
            },
        )
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/support"


def _http_error_with_native_detail(native_detail):
    resp = requests.Response()
    resp.status_code = 400
    resp.json = lambda: {"detail": {"code": "some_error", "native_detail": native_detail}}
    return requests.exceptions.HTTPError(response=resp)


def test_profile_update_shows_native_error_message(logged_in_client):
    err = _http_error_with_native_detail("L'alias mail1@byrtn.fr est déjà utilisé par un autre compte")
    with patch.object(app, "_wappos_api_me", return_value={"username": "patrick", "fullname": "Patrick Ritaine", "mail": "patrick@byrtn.fr", "mailalias": [], "mailforward": [], "groups": ["all_users"]}), \
         patch.object(app, "_wappos_api_update", side_effect=err):
        resp = logged_in_client.post("/profile", data={"action": "update_info", "fullname": "Patrick"})
    assert resp.status_code == 200
    assert b"d\xc3\xa9j\xc3\xa0 utilis\xc3\xa9" in resp.data


def test_profile_update_falls_back_to_generic_message_without_native_detail(logged_in_client):
    with patch.object(app, "_wappos_api_me", return_value={"username": "patrick", "fullname": "Patrick Ritaine", "mail": "patrick@byrtn.fr", "mailalias": [], "mailforward": [], "groups": ["all_users"]}), \
         patch.object(app, "_wappos_api_update", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.post("/profile", data={"action": "update_info", "fullname": "Patrick"})
    assert resp.status_code == 200
    assert "la modification a échoué".encode() in resp.data.lower()


def test_domain_default_theme_is_injected_in_page(client):
    with patch.object(app, "_public_settings_safe", return_value={"portal_theme": "dark"}):
        resp = client.get("/")
    assert resp.status_code == 200
    assert b'var domainDefault = "dark"' in resp.data


def test_domain_default_theme_defaults_to_system(client):
    with patch.object(app, "_public_settings_safe", return_value={}):
        resp = client.get("/")
    assert resp.status_code == 200
    assert b'var domainDefault = "system"' in resp.data


def test_logout_clears_session(logged_in_client):
    with patch.object(app, "_wappos_api_logout", return_value=None):
        resp = logged_in_client.post("/logout")
    assert resp.status_code == 302
    with logged_in_client.session_transaction() as sess:
        assert "user" not in sess


def test_reorder_requires_authentication(client):
    resp = client.post("/reorder", json={"order": ["a.main"]})
    assert resp.status_code == 401


def test_reorder_rejects_invalid_payload(logged_in_client):
    resp = logged_in_client.post("/reorder", json={"order": "not-a-list"})
    assert resp.status_code == 400


def test_reorder_saves_order(monkeypatch, tmp_path, logged_in_client):
    monkeypatch.setattr(app, "TILE_ORDER_DIR", tmp_path)
    resp = logged_in_client.post("/reorder", json={"order": ["b.main", "a.main"]})
    assert resp.status_code == 200
    assert app._load_order("patrick") == ["b.main", "a.main"]


def test_documentation_requires_authentication_redirects(client):
    resp = client.get("/documentation")
    assert resp.status_code == 302


def test_documentation_authenticated_renders(logged_in_client):
    resp = logged_in_client.get("/documentation")
    assert resp.status_code == 200


def test_set_language_sets_cookie(client):
    resp = client.get("/set_language/en")
    assert resp.status_code == 302
    assert resp.headers.get("Set-Cookie", "").startswith("wappos_portal_lang=en")


def test_login_clears_stale_portal_cookie_variants_before_setting_fresh_one(client):
    fresh_cookie = "yunohost.portal=freshvalue; Domain=localhost; Path=/; Secure; HttpOnly"
    with patch.object(app, "_wappos_api_login", return_value=("tok123", fresh_cookie)):
        resp = client.post("/login", data={"username": "patrick", "password": "secret"})
    set_cookie_headers = resp.headers.get_all("Set-Cookie")
    portal_cookie_headers = [h for h in set_cookie_headers if h.startswith("yunohost.portal=")]
    assert len(portal_cookie_headers) == 3
    assert sum(1 for h in portal_cookie_headers if "freshvalue" in h) == 1
    assert sum(1 for h in portal_cookie_headers if "1970" in h) == 2
