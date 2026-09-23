# Auteur : Patrick Ritaine
from unittest.mock import patch

import app
import docker_gate as dg


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


def test_environment_health_shows_certificates_diagnosis_disk_and_docker(logged_in_client):
    certificates = {"dev.byrtn.fr": {"CA_type": "letsencrypt", "validity": 76, "style": "success", "summary": "letsencrypt"}}
    reports = [{"id": "web", "error_count": 1, "warning_count": 2}]
    apps = [{"id": "grav", "label": "Grav | actus"}]
    docker_apps = [{"slug": "grafana", "domain": "dev.byrtn.fr", "path": "/grafana", "container_status": "running"}]

    with patch.object(app, "_wappos_api_domains_certificates", return_value=certificates), \
         patch.object(app, "_wappos_api_admin_diagnosis", return_value=reports), \
         patch.object(app, "_wappos_api_admin_apps", return_value=apps), \
         patch.object(app, "_wappos_api_app_disk_usage", return_value=1048576), \
         patch.object(dg, "list_apps", return_value=docker_apps):
        resp = logged_in_client.get("/environment")

    body = resp.data.decode()
    assert resp.status_code == 200
    assert "dev.byrtn.fr" in body
    assert "Grav | actus" in body
    assert "grafana" in body


def test_environment_health_filters_docker_apps_for_domain_admin(client, monkeypatch):
    _domain_admin_client(client, ["dev.byrtn.fr"], monkeypatch)
    docker_apps = [
        {"slug": "grafana", "domain": "dev.byrtn.fr", "path": "/grafana", "container_status": "running"},
        {"slug": "other", "domain": "dev.wappos.fr", "path": "/other", "container_status": "running"},
    ]

    with patch.object(app, "_wappos_api_domains_certificates", return_value={}), \
         patch.object(app, "_wappos_api_admin_diagnosis", return_value=[]), \
         patch.object(app, "_wappos_api_admin_apps", return_value=[]), \
         patch.object(dg, "list_apps", return_value=docker_apps):
        resp = client.get("/environment")

    body = resp.data.decode()
    assert resp.status_code == 200
    assert "grafana" in body
    assert "other" not in body
