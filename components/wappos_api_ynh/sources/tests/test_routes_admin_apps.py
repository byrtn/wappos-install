from __future__ import annotations
# Auteur : Patrick Ritaine

import respx
from fastapi.testclient import TestClient
from httpx import Response

from wappos_api.main import app

client = TestClient(app)


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
