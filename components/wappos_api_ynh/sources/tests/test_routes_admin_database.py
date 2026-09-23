from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
from fastapi.testclient import TestClient

from wappos_api import scope as scope_module
from wappos_api.connectors import admin as admin_connector
from wappos_api.connectors import db_access as db_access_connector
from wappos_api.main import app
from wappos_api.schemas.app import AppInfo

client = TestClient(app)


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


_APPS = [
    AppInfo(id="nextcloud", name="Nextcloud", label="Nextcloud", description="", version="1", domain_path="dev.byrtn.fr/nextcloud"),
    AppInfo(id="roundcube", name="Roundcube", label="Roundcube", description="", version="1", domain_path="dev.wappos.fr/mail"),
    AppInfo(id="static_site", name="Static", label="Static", description="", version="1", domain_path="dev.byrtn.fr/static"),
]

_DB_MAP = {
    "nextcloud": {"db_name": "nextcloud", "db_user": "nextcloud"},
    "roundcube": {"db_name": "roundcube", "db_user": "roundcube"},
}


def test_list_database_apps_as_superadmin_returns_all_apps_with_a_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(admin_connector, "list_apps", lambda token: _APPS)
    monkeypatch.setattr(db_access_connector, "list_all", lambda: _DB_MAP)

    response = client.get("/admin/database/apps", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    ids = {entry["app_id"] for entry in response.json()}
    assert ids == {"nextcloud", "roundcube"}


def test_list_database_apps_as_domain_admin_filters_by_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])
    monkeypatch.setattr(admin_connector, "list_apps", lambda t: _APPS)
    monkeypatch.setattr(db_access_connector, "list_all", lambda: _DB_MAP)

    response = client.get("/admin/database/apps", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    ids = {entry["app_id"] for entry in response.json()}
    assert ids == {"nextcloud"}


def test_get_database_credentials_forbidden_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])
    monkeypatch.setattr(scope_module, "resolve_app_domains", lambda t, app_id: ["dev.wappos.fr"])

    response = client.get("/admin/database/apps/roundcube/credentials", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_get_database_credentials_allowed_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])
    monkeypatch.setattr(scope_module, "resolve_app_domains", lambda t, app_id: ["dev.byrtn.fr"])
    monkeypatch.setattr(
        db_access_connector,
        "get_credentials",
        lambda app_id: {"db_name": "nextcloud", "db_user": "nextcloud", "db_pwd": "secret"},
    )

    response = client.get("/admin/database/apps/nextcloud/credentials", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert response.json() == {"db_name": "nextcloud", "db_user": "nextcloud", "db_pwd": "secret"}


def test_get_database_credentials_returns_404_when_app_has_no_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(db_access_connector, "get_credentials", lambda app_id: None)

    response = client.get("/admin/database/apps/static_site/credentials", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 404
