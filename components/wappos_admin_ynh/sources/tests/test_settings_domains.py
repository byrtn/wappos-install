# Auteur : Patrick Ritaine
from unittest.mock import patch

import requests

import app


def _http_error_with_detail(code, native_detail=None):
    resp = requests.Response()
    resp.status_code = 400
    payload = {"detail": {"code": code}}
    if native_detail:
        payload["detail"]["native_detail"] = native_detail
    resp.json = lambda: payload
    return requests.exceptions.HTTPError(response=resp)


def test_settings_page_requires_authentication(client):
    resp = client.get("/settings")
    assert resp.status_code == 401


def test_settings_page_renders_panels(logged_in_client):
    with patch.object(app, "_wappos_api_settings", return_value={"panels": []}):
        resp = logged_in_client.get("/settings")
    assert resp.status_code == 200


def test_settings_page_api_unreachable_returns_503(logged_in_client):
    with patch.object(app, "_wappos_api_settings", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.get("/settings")
    assert resp.status_code == 503


def test_domains_page_requires_authentication(client):
    resp = client.get("/domains")
    assert resp.status_code == 401


def test_domains_page_renders_domain_list(logged_in_client):
    with patch.object(app, "_wappos_api_domains", return_value=["byrtn.fr"]), \
         patch.object(app, "_wappos_api_adguard_status", return_value={"installed": False}), \
         patch.object(app, "_wappos_api_certificates_status", return_value={}):
        resp = logged_in_client.get("/domains")
    assert resp.status_code == 200


def test_domains_page_shows_certificate_validity(logged_in_client):
    certs = {"byrtn.fr": {"CA_type": "letsencrypt", "validity": 42, "style": "success", "summary": "letsencrypt"}}
    with patch.object(app, "_wappos_api_domains", return_value=["byrtn.fr"]), \
         patch.object(app, "_wappos_api_adguard_status", return_value={"installed": False}), \
         patch.object(app, "_wappos_api_certificates_status", return_value=certs):
        resp = logged_in_client.get("/domains")
    assert resp.status_code == 200
    assert b"42 jours" in resp.data


def test_domain_add_success_redirects_to_detail(logged_in_client):
    with patch.object(app, "_wappos_api_add_domain", return_value=None):
        resp = logged_in_client.post("/domains/add", data={"domain": "new.byrtn.fr"})
    assert resp.status_code == 302
    assert "new.byrtn.fr" in resp.headers["Location"]


def test_domain_add_already_exists_redirects_with_error(logged_in_client):
    err = _http_error_with_detail("domain_exists")
    with patch.object(app, "_wappos_api_add_domain", side_effect=err):
        resp = logged_in_client.post("/domains/add", data={"domain": "byrtn.fr"})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_group_domains_by_parent_nests_subdomains():
    groups = app._group_domains_by_parent(
        ["byrtn.fr", "adguard.byrtn.fr", "photography.byrtn.fr", "wappos.fr"]
    )
    by_domain = {g["domain"]: g["children"] for g in groups}
    assert by_domain["byrtn.fr"] == ["adguard.byrtn.fr", "photography.byrtn.fr"]
    assert by_domain["wappos.fr"] == []


def test_group_domains_by_parent_flattens_multi_level_subdomains_under_root():
    groups = app._group_domains_by_parent(["byrtn.fr", "dev.byrtn.fr", "app.dev.byrtn.fr"])
    assert len(groups) == 1
    assert groups[0]["domain"] == "byrtn.fr"
    assert groups[0]["children"] == ["app.dev.byrtn.fr", "dev.byrtn.fr"]


def test_group_domains_by_parent_no_domain_ever_dropped():
    domains = ["byrtn.fr", "dev.byrtn.fr", "app.dev.byrtn.fr", "wappos.fr"]
    groups = app._group_domains_by_parent(domains)
    all_rendered = {g["domain"] for g in groups} | {c for g in groups for c in g["children"]}
    assert all_rendered == set(domains)


def test_domain_remove_forwards_dyndns_recovery_password(logged_in_client):
    with patch.object(app, "_wappos_api_remove_domain", return_value=None) as mocked:
        resp = logged_in_client.post(
            "/domains/foo.nohost.me/remove", data={"dyndns_recovery_password": "secret123"}
        )
    assert resp.status_code == 302
    assert mocked.call_args.kwargs["dyndns_recovery_password"] == "secret123"


def test_domains_page_lists_local_domains_separately(logged_in_client):
    with patch.object(app, "_wappos_api_domains", return_value=["byrtn.fr", "wappos.lan"]), \
         patch.object(app, "_wappos_api_adguard_status", return_value={"installed": True}), \
         patch.object(app, "_wappos_api_certificates_status", return_value={}):
        resp = logged_in_client.get("/domains")
    assert resp.status_code == 200
    assert b"wappos.lan" in resp.data


def test_local_domain_add_success_redirects_with_message(logged_in_client):
    with patch.object(
        app, "_wappos_api_add_local_domain",
        return_value={"domain": "wappos.lan", "domain_added": True, "adguard_rewrite_added": True},
    ):
        resp = logged_in_client.post("/domains/local/add", data={"domain": "wappos.lan"})
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]


def test_local_domain_add_adguard_failure_redirects_with_error(logged_in_client):
    with patch.object(
        app, "_wappos_api_add_local_domain",
        return_value={"domain": "wappos.lan", "domain_added": True, "adguard_rewrite_added": False},
    ):
        resp = logged_in_client.post("/domains/local/add", data={"domain": "wappos.lan"})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_local_domain_add_invalid_name_redirects_with_error(logged_in_client):
    err = _http_error_with_detail("invalid_local_domain")
    with patch.object(app, "_wappos_api_add_local_domain", side_effect=err):
        resp = logged_in_client.post("/domains/local/add", data={"domain": "not-local.fr"})
    assert resp.status_code == 302
    assert "error=" in resp.headers["Location"]


def test_local_domain_remove_success_redirects_with_message(logged_in_client):
    with patch.object(
        app, "_wappos_api_remove_local_domain",
        return_value={"domain": "wappos.lan", "domain_added": False, "adguard_rewrite_added": True},
    ):
        resp = logged_in_client.post("/domains/local/wappos.lan/remove")
    assert resp.status_code == 302
    assert "msg=" in resp.headers["Location"]


def test_app_map_page_requires_authentication(client):
    resp = client.get("/app-map")
    assert resp.status_code == 401


def test_app_map_page_renders_map(logged_in_client):
    with patch.object(app, "_wappos_api_app_map", return_value={"byrtn.fr": {"/": {"id": "grav", "label": "Grav"}}}):
        resp = logged_in_client.get("/app-map")
    assert resp.status_code == 200


def test_app_map_page_api_unreachable_returns_503(logged_in_client):
    with patch.object(app, "_wappos_api_app_map", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.get("/app-map")
    assert resp.status_code == 503


def test_domain_url_available_requires_authentication(client):
    resp = client.get("/domains/urlavailable", query_string={"domain": "byrtn.fr", "path": "/foo"})
    assert resp.status_code == 401


def test_domain_url_available_missing_params_returns_none(logged_in_client):
    resp = logged_in_client.get("/domains/urlavailable")
    assert resp.status_code == 200
    assert resp.get_json() == {"available": None}


def test_domain_url_available_true(logged_in_client):
    with patch.object(app, "_wappos_api_domain_url_available", return_value=True):
        resp = logged_in_client.get("/domains/urlavailable", query_string={"domain": "byrtn.fr", "path": "/foo"})
    assert resp.get_json() == {"available": True}


def test_domain_url_available_api_error_returns_none(logged_in_client):
    with patch.object(app, "_wappos_api_domain_url_available", side_effect=requests.exceptions.ConnectionError()):
        resp = logged_in_client.get("/domains/urlavailable", query_string={"domain": "byrtn.fr", "path": "/foo"})
    assert resp.get_json() == {"available": None}
