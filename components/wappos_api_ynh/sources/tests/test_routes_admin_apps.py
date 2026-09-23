from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.connectors import admin as admin_connector
from wappos_api.main import app

client = TestClient(app)


def _domain_admin_token(monkeypatch: pytest.MonkeyPatch, owned_domains: list[str]) -> str:
    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: owned_domains
    )
    monkeypatch.setattr(admin_connector, "_service_session_token", lambda: "service-session-token")
    return token


@respx.mock
def test_apps_returns_installed_apps(admin_login_url: str) -> None:
    apps_url = admin_login_url.replace("/login", "/apps")
    respx.get(apps_url).mock(
        return_value=Response(
            200,
            json={
                "apps": [
                    {
                        "id": "wappos_admin",
                        "name": "Wappos Admin",
                        "description": "Portail d'administration Wappos",
                        "version": "0.1.04~ynh1",
                        "domain_path": "dev.byrtn.fr/wappos-admin",
                        "logo": "abc123hash",
                    }
                ]
            },
        )
    )

    response = client.get("/admin/apps", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "wappos_admin",
            "name": "Wappos Admin",
            "label": "Wappos Admin",
            "description": "Portail d'administration Wappos",
            "version": "0.1.04~ynh1",
            "domain_path": "dev.byrtn.fr/wappos-admin",
            "logo": "abc123hash",
        }
    ]
    assert respx.calls.last.request.url.params["full"] == ""


@respx.mock
def test_apps_rejects_invalid_session(admin_login_url: str) -> None:
    apps_url = admin_login_url.replace("/login", "/apps")
    respx.get(apps_url).mock(return_value=Response(401))

    response = client.get("/admin/apps", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401


@respx.mock
def test_app_detail_returns_full_info(admin_login_url: str) -> None:
    app_url = admin_login_url.replace("/login", "/apps/wappos_admin")
    respx.get(app_url).mock(
        return_value=Response(
            200,
            json={
                "id": "wappos_admin",
                "name": "Wappos Admin",
                "label": "Wappos Admin",
                "description": "Portail d'administration Wappos",
                "version": "0.1.31~ynh1",
                "upgrade": {
                    "status": "up_to_date",
                    "message": "Already up to date",
                    "current_version": "0.1.31~ynh1",
                    "new_version": "0.1.31~ynh1",
                },
            },
        )
    )

    response = client.get("/admin/apps/wappos_admin", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["id"] == "wappos_admin"
    assert response.json()["upgrade"]["status"] == "up_to_date"


@respx.mock
def test_app_detail_rejects_invalid_session(admin_login_url: str) -> None:
    app_url = admin_login_url.replace("/login", "/apps/wappos_admin")
    respx.get(app_url).mock(return_value=Response(401))

    response = client.get("/admin/apps/wappos_admin", headers={"X-Admin-Token": "expired-token"})

    assert response.status_code == 401


@respx.mock
def test_apps_catalog_route_not_shadowed_by_app_id_route(admin_login_url: str) -> None:
    catalog_url = admin_login_url.replace("/login", "/apps/catalog")
    respx.get(catalog_url).mock(return_value=Response(200, json={"apps": {}, "categories": []}))

    response = client.get("/admin/apps/catalog", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"apps": [], "categories": [], "antifeatures": []}


@respx.mock
def test_apps_manifest_route_not_shadowed_by_app_id_route(admin_login_url: str) -> None:
    manifest_url = admin_login_url.replace("/login", "/apps/manifest")
    respx.get(manifest_url).mock(
        return_value=Response(200, json={"id": "roundcube", "name": "Roundcube", "install": []})
    )

    response = client.get("/admin/apps/manifest", params={"app_id": "roundcube"}, headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json()["id"] == "roundcube"


@respx.mock
def test_install_app_route_posts_json_body(admin_login_url: str) -> None:
    apps_url = admin_login_url.replace("/login", "/apps")
    route = respx.post(apps_url).mock(return_value=Response(200, json={}))

    response = client.post(
        "/admin/apps",
        json={"app": "roundcube", "label": "Mail", "args": "domain=x&path=/y"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 200
    assert route.called


@respx.mock
def test_remove_app_route_returns_204(admin_login_url: str) -> None:
    remove_url = admin_login_url.replace("/login", "/apps/roundcube")
    respx.delete(remove_url).mock(return_value=Response(200))

    response = client.delete("/admin/apps/roundcube", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_upgrade_app_route_returns_json(admin_login_url: str) -> None:
    upgrade_url = admin_login_url.replace("/login", "/apps/roundcube/upgrade")
    respx.put(upgrade_url).mock(return_value=Response(200, json={}))

    response = client.put("/admin/apps/roundcube/upgrade", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200


@respx.mock
def test_change_app_url_route_returns_204(admin_login_url: str) -> None:
    changeurl_url = admin_login_url.replace("/login", "/apps/roundcube/changeurl")
    respx.put(changeurl_url).mock(return_value=Response(200))

    response = client.put(
        "/admin/apps/roundcube/changeurl",
        json={"domain": "dev.byrtn.fr", "path": "/mail"},
        headers={"X-Admin-Token": "abc123"},
    )

    assert response.status_code == 204


@respx.mock
def test_app_actions_route_returns_raw_payload(admin_login_url: str) -> None:
    actions_url = admin_login_url.replace("/login", "/apps/roundcube/actions")
    respx.get(actions_url).mock(return_value=Response(200, json={"actions": []}))

    response = client.get("/admin/apps/roundcube/actions", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"actions": []}


@respx.mock
def test_app_config_route_returns_raw_payload(admin_login_url: str) -> None:
    config_url = admin_login_url.replace("/login", "/apps/roundcube/config")
    respx.get(config_url).mock(return_value=Response(200, json={"panels": []}))

    response = client.get("/admin/apps/roundcube/config", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"panels": []}


@respx.mock
def test_domains_returns_list(admin_login_url: str) -> None:
    domains_url = admin_login_url.replace("/login", "/domains")
    respx.get(domains_url).mock(return_value=Response(200, json={"domains": ["dev.byrtn.fr"], "main": "dev.byrtn.fr"}))

    response = client.get("/admin/domains", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == ["dev.byrtn.fr"]


@respx.mock
def test_app_map_route_not_shadowed_by_app_id_route(admin_login_url: str) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(return_value=Response(200, json={"dev.byrtn.fr/foo": "grav"}))

    response = client.get("/admin/apps/map", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 200
    assert response.json() == {"dev.byrtn.fr/foo": "grav"}


@respx.mock
def test_app_makedefault_route_returns_204(admin_login_url: str) -> None:
    makedefault_url = admin_login_url.replace("/login", "/apps/roundcube/default")
    respx.put(makedefault_url).mock(return_value=Response(200))

    response = client.put("/admin/apps/roundcube/default", headers={"X-Admin-Token": "abc123"})

    assert response.status_code == 204


@respx.mock
def test_apps_list_filtered_for_domain_admin(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    apps_url = admin_login_url.replace("/login", "/apps")
    respx.get(apps_url).mock(
        return_value=Response(
            200,
            json={
                "apps": [
                    {
                        "id": "grav",
                        "name": "Grav",
                        "description": "",
                        "version": "1.0",
                        "domain_path": "dev.byrtn.fr/actus",
                        "logo": None,
                    },
                    {
                        "id": "roundcube",
                        "name": "Roundcube",
                        "description": "",
                        "version": "1.0",
                        "domain_path": "dev.wappos.fr/webmail",
                        "logo": None,
                    },
                ]
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert [a["id"] for a in response.json()] == ["grav"]


@respx.mock
def test_app_detail_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps/roundcube", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_app_detail_allowed_inside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    detail_url = admin_login_url.replace("/login", "/apps/grav")
    respx.get(detail_url).mock(
        return_value=Response(
            200,
            json={
                "id": "grav",
                "name": "Grav",
                "version": "1.0",
                "description": "",
            },
        )
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps/grav", headers={"X-Admin-Token": token})

    assert response.status_code == 200


@respx.mock
def test_install_app_forbidden_when_app_has_no_domain_arg(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_url = admin_login_url.replace("/login", "/apps/manifest")
    respx.get(manifest_url).mock(
        return_value=Response(200, json={"id": "some_tool", "name": "Some Tool", "install": []})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/apps", json={"app": "some_tool", "args": "foo=bar"}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_install_app_forbidden_when_domain_missing_from_args(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_url = admin_login_url.replace("/login", "/apps/manifest")
    respx.get(manifest_url).mock(
        return_value=Response(200, json={"id": "grav", "name": "Grav", "install": [{"id": "domain"}]})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/apps", json={"app": "grav", "args": "path=/actus"}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_install_app_forbidden_for_domain_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_url = admin_login_url.replace("/login", "/apps/manifest")
    respx.get(manifest_url).mock(
        return_value=Response(200, json={"id": "grav", "name": "Grav", "install": [{"id": "domain"}]})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/apps", json={"app": "grav", "args": "domain=dev.wappos.fr"}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_install_app_allowed_for_domain_in_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    manifest_url = admin_login_url.replace("/login", "/apps/manifest")
    respx.get(manifest_url).mock(
        return_value=Response(200, json={"id": "grav", "name": "Grav", "install": [{"id": "domain"}]})
    )
    apps_url = admin_login_url.replace("/login", "/apps")
    respx.post(apps_url).mock(return_value=Response(200, json={}))
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.post(
        "/admin/apps", json={"app": "grav", "args": "domain=dev.byrtn.fr&path=/actus"},
        headers={"X-Admin-Token": token},
    )

    assert response.status_code == 200


def test_cross_domain_status_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps/roundcube/cross-domain", headers={"X-Admin-Token": token})

    assert response.status_code == 403


def test_cross_domain_set_forbidden_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.put(
        "/admin/apps/roundcube/cross-domain", json={"enabled": True}, headers={"X-Admin-Token": token}
    )

    assert response.status_code == 403


@respx.mock
def test_disk_usage_forbidden_outside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}}})
    )
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    response = client.get("/admin/apps/roundcube/disk-usage", headers={"X-Admin-Token": token})

    assert response.status_code == 403


@respx.mock
def test_disk_usage_allowed_inside_scope(admin_login_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    map_url = admin_login_url.replace("/login", "/apps/map")
    respx.get(map_url).mock(
        return_value=Response(200, json={"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}})
    )
    detail_url = admin_login_url.replace("/login", "/apps/grav")
    respx.get(detail_url).mock(
        return_value=Response(200, json={"id": "grav", "settings": {"install_dir": "/var/www/grav"}})
    )
    from unittest.mock import patch

    from wappos_api.connectors import admin as admin_connector
    token = _domain_admin_token(monkeypatch, ["dev.byrtn.fr"])

    with patch.object(admin_connector, "_dir_size_bytes", return_value=500):
        response = client.get("/admin/apps/grav/disk-usage", headers={"X-Admin-Token": token})

    assert response.status_code == 200
    assert response.json() == {"bytes": 500}
