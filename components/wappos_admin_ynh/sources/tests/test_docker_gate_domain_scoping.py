# Auteur : Patrick Ritaine
from unittest.mock import patch

import app
import docker_gate as dg


def _entry(domain="dev.byrtn.fr"):
    return {
        "slug": "grafana", "yunohost_app_id": "redirect__3",
        "image": "grafana/grafana", "container_port": "3000",
        "data_path": "/var/lib/grafana", "cpu_limit": "", "mem_limit": "",
        "domain": domain, "path": "/grafana",
    }


def _domain_admin_client(client, owned_domains, monkeypatch):
    with client.session_transaction() as sess:
        sess["user"] = "domain.admin"
        sess["token"] = "test-token"
        sess["is_superadmin"] = False
        sess["owned_domains"] = owned_domains
    monkeypatch.setattr(
        app, "_wappos_api_admin_session",
        lambda token: {"is_superadmin": False, "owned_domains": owned_domains},
    )
    return client


def test_docker_apps_list_filtered_by_owned_domain(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    apps = [
        {"slug": "grafana", "domain": "dev.byrtn.fr"},
        {"slug": "other", "domain": "other.byrtn.fr"},
    ]
    with patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(dg, "list_apps", return_value=apps):
        resp = client.get("/docker")
    body = resp.data.decode()
    assert resp.status_code == 200
    assert "grafana" in body
    assert "other" not in body


def test_docker_apps_list_not_filtered_for_superadmin(logged_in_client):
    apps = [
        {"slug": "grafana", "domain": "dev.byrtn.fr"},
        {"slug": "other", "domain": "other.byrtn.fr"},
    ]
    with patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(dg, "list_apps", return_value=apps):
        resp = logged_in_client.get("/docker")
    body = resp.data.decode()
    assert "grafana" in body
    assert "other" in body


def test_docker_edit_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.get("/docker/edit/grafana")
    assert resp.status_code == 403


def test_docker_edit_allowed_for_domain_admin_in_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="dev.byrtn.fr"))
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    resp = client.get("/docker/edit/grafana")
    assert resp.status_code == 200


def test_docker_edit_allowed_for_domain_admin_on_subdomain(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="app.dev.byrtn.fr"))
    monkeypatch.setattr(dg, "read_current_env_vars", lambda slug: {})
    resp = client.get("/docker/edit/grafana")
    assert resp.status_code == 200


def test_docker_remove_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.post("/docker/remove/grafana", data={})
    assert resp.status_code == 403


def test_docker_action_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.post("/docker/action/grafana/start")
    assert resp.status_code == 403


def test_docker_logs_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.get("/docker/logs/grafana")
    assert resp.status_code == 403


def test_docker_stats_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.get("/docker/stats/grafana")
    assert resp.status_code == 403


def test_docker_change_url_forbidden_for_domain_admin_out_of_scope(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    resp = client.post("/docker/change_url/grafana", data={"domain": "dev.byrtn.fr", "path": "/x"})
    assert resp.status_code == 403


def test_docker_add_forbidden_for_domain_admin_out_of_scope_path_mode(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.post("/docker/add", data={
        "slug": "grafana", "image": "grafana/grafana", "container_port": "3000",
        "mode": "path", "domain": "other.byrtn.fr", "path": "/grafana",
    })
    assert resp.status_code == 403


def test_docker_add_forbidden_for_domain_admin_out_of_scope_subdomain_mode(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.post("/docker/add", data={
        "slug": "grafana", "image": "grafana/grafana", "container_port": "3000",
        "mode": "subdomain", "domain_parent": "other.byrtn.fr", "new_subdomain": "grafana",
    })
    assert resp.status_code == 403


def test_docker_audit_forbidden_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.get("/docker/audit")
    assert resp.status_code == 403


def test_docker_audit_prune_images_forbidden_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.post("/docker/audit/prune_images")
    assert resp.status_code == 403


def test_docker_audit_uninstall_docker_ce_forbidden_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.post("/docker/audit/uninstall_docker_ce")
    assert resp.status_code == 403


def test_docker_check_subdomain_invalid_for_out_of_scope_parent(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.get("/docker/check_subdomain", query_string={"new_subdomain": "app", "domain_parent": "other.byrtn.fr"})
    assert resp.get_json() == {"status": "invalid"}


def test_docker_check_path_invalid_for_out_of_scope_domain(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    resp = client.get("/docker/check_path", query_string={"domain": "other.byrtn.fr", "path": "/x"})
    assert resp.get_json() == {"status": "invalid"}


def test_docker_action_uses_live_scope_not_stale_session(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    with patch.object(
        app, "_wappos_api_admin_session",
        return_value={"is_superadmin": False, "owned_domains": ["dev.byrtn.fr", "other.byrtn.fr"]},
    ), patch.object(dg, "container_action", return_value=None):
        resp = client.post("/docker/action/grafana/start")
    assert resp.status_code == 302
    with client.session_transaction() as sess:
        assert sess["owned_domains"] == ["dev.byrtn.fr", "other.byrtn.fr"]


def test_docker_action_revoked_domain_blocked_even_with_stale_cached_session(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr", "other.byrtn.fr"], monkeypatch)
    monkeypatch.setattr(dg, "get_app_entry", lambda slug, **kwargs: _entry(domain="other.byrtn.fr"))
    with patch.object(
        app, "_wappos_api_admin_session",
        return_value={"is_superadmin": False, "owned_domains": ["dev.byrtn.fr"]},
    ):
        resp = client.post("/docker/action/grafana/start")
    assert resp.status_code == 403
