from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_apps_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/apps")


@respx.mock
def test_list_apps_parses_real_shape(admin_apps_url: str) -> None:
    respx.get(admin_apps_url).mock(
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
                    },
                    {
                        "id": "wappos_api",
                        "name": "Wappos API",
                        "description": "Service API interne",
                        "version": "0.1.04~ynh1",
                    },
                ]
            },
        )
    )

    apps = admin.list_apps("fake-session-token")

    assert {a.id for a in apps} == {"wappos_admin", "wappos_api"}
    assert apps[0].domain_path == "dev.byrtn.fr/wappos-admin"
    assert apps[1].domain_path is None


@respx.mock
def test_list_apps_sorted_by_name_not_api_order(admin_apps_url: str) -> None:
    respx.get(admin_apps_url).mock(
        return_value=Response(
            200,
            json={
                "apps": [
                    {"id": "zzz_app", "name": "Alpha App", "description": "", "version": "1.0"},
                    {"id": "aaa_app", "name": "Zebra App", "description": "", "version": "1.0"},
                ]
            },
        )
    )

    apps = admin.list_apps("fake-session-token")

    assert [a.name for a in apps] == ["Alpha App", "Zebra App"]


@respx.mock
def test_list_apps_rejects_invalid_session(admin_apps_url: str) -> None:
    respx.get(admin_apps_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_apps("expired-token")


@respx.mock
def test_list_apps_unexpected_shape_raises_protocol_error(admin_apps_url: str) -> None:
    respx.get(admin_apps_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.list_apps("fake-session-token")


@pytest.fixture
def admin_app_detail_url(admin_apps_url: str) -> str:
    return f"{admin_apps_url}/wappos_admin"


@respx.mock
def test_get_app_detail_parses_real_shape(admin_app_detail_url: str) -> None:
    respx.get(admin_app_detail_url).mock(
        return_value=Response(
            200,
            json={
                "id": "wappos_admin",
                "name": "Wappos Admin",
                "label": "Wappos Admin",
                "description": "Portail d'administration Wappos",
                "version": "0.1.31~ynh1",
                "domain_path": "dev.byrtn.fr/wappos-admin",
                "logo": "wappos_admin",
                "is_webapp": True,
                "supports_change_url": True,
                "supports_purge": True,
                "upgrade": {
                    "status": "up_to_date",
                    "message": "Already up to date",
                    "current_version": "0.1.31~ynh1",
                    "new_version": "0.1.31~ynh1",
                },
            },
        )
    )

    detail = admin.get_app_detail("fake-session-token", "wappos_admin")

    assert detail.id == "wappos_admin"
    assert detail.label == "Wappos Admin"
    assert detail.upgrade.status == "up_to_date"
    assert detail.is_webapp is True
    assert detail.supports_change_url is True


@respx.mock
def test_get_app_detail_rejects_invalid_session(admin_app_detail_url: str) -> None:
    respx.get(admin_app_detail_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_app_detail("expired-token", "wappos_admin")


@respx.mock
def test_get_app_detail_unexpected_shape_raises_protocol_error(admin_app_detail_url: str) -> None:
    respx.get(admin_app_detail_url).mock(return_value=Response(200, json={"unexpected": "shape"}))

    with pytest.raises(UpstreamProtocolError):
        admin.get_app_detail("fake-session-token", "wappos_admin")


@respx.mock
def test_get_app_detail_picks_notifications(admin_app_detail_url: str) -> None:
    respx.get(admin_app_detail_url).mock(
        return_value=Response(
            200,
            json={
                "id": "wappos_admin",
                "name": "Wappos Admin",
                "version": "0.1.32~ynh1",
                "supports_config_panel": True,
                "manifest": {
                    "notifications": {
                        "POST_INSTALL": {"main": {"fr": "Bienvenue", "en": "Welcome"}},
                        "POST_UPGRADE": {"main": {"en": "Upgraded"}},
                    }
                },
            },
        )
    )

    detail = admin.get_app_detail("fake-session-token", "wappos_admin")

    assert detail.notification_post_install == "Bienvenue"
    assert detail.notifications_post_upgrade == {"main": "Upgraded"}
    assert detail.supports_config_panel is True


@respx.mock
def test_install_app_posts_correct_payload(admin_apps_url: str) -> None:
    route = respx.post(admin_apps_url).mock(return_value=Response(200, json={}))

    admin.install_app("fake-session-token", "roundcube", label="Mail", args="domain=x&path=/y")

    assert route.called
    body = route.calls.last.request.content
    import json as _json

    assert _json.loads(body) == {"app": "roundcube", "label": "Mail", "args": "domain=x&path=/y", "force": False}


@respx.mock
def test_install_app_rejects_invalid_session(admin_apps_url: str) -> None:
    respx.post(admin_apps_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.install_app("expired-token", "roundcube")


@respx.mock
def test_remove_app_calls_delete(admin_apps_url: str) -> None:
    route = respx.delete(f"{admin_apps_url}/roundcube").mock(return_value=Response(200))

    admin.remove_app("fake-session-token", "roundcube", purge=True)

    assert route.called
    assert route.calls.last.request.url.params["purge"] == "1"
    import json as _json

    assert _json.loads(route.calls.last.request.content)["app"] == "roundcube"


@respx.mock
def test_upgrade_app_calls_put(admin_apps_url: str) -> None:
    route = respx.put(f"{admin_apps_url}/roundcube/upgrade").mock(return_value=Response(200, json={}))

    admin.upgrade_app("fake-session-token", "roundcube")

    assert route.called


@respx.mock
def test_change_app_url_calls_put(admin_apps_url: str) -> None:
    route = respx.put(f"{admin_apps_url}/roundcube/changeurl").mock(return_value=Response(200))

    admin.change_app_url("fake-session-token", "roundcube", "dev.byrtn.fr", "/mail")

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content)["app"] == "roundcube"


@respx.mock
def test_change_app_label_calls_put(admin_apps_url: str) -> None:
    route = respx.put(f"{admin_apps_url}/roundcube/label").mock(return_value=Response(200))

    admin.change_app_label("fake-session-token", "roundcube", "Ma boîte mail")

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content)["app"] == "roundcube"


@respx.mock
def test_dismiss_app_notification_calls_put(admin_apps_url: str) -> None:
    route = respx.put(f"{admin_apps_url}/roundcube/dismiss_notification/post_install").mock(
        return_value=Response(200)
    )

    admin.dismiss_app_notification("fake-session-token", "roundcube", "post_install")

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["app"] == "roundcube"
    assert body["name"] == "post_install"


@pytest.fixture
def admin_apps_catalog_url(admin_apps_url: str) -> str:
    return f"{admin_apps_url}/catalog"


@respx.mock
def test_get_app_catalog_parses_and_sorts(admin_apps_catalog_url: str) -> None:
    respx.get(admin_apps_catalog_url).mock(
        return_value=Response(
            200,
            json={
                "apps": {
                    "zzz_app": {
                        "manifest": {"name": "Alpha", "description": "A"},
                        "level": 8,
                        "installed": False,
                        "category": "publishing",
                        "subtags": ["website"],
                        "maintained": True,
                        "state": "working",
                    },
                    "aaa_app": {
                        "manifest": {"name": "Zebra", "description": "Z"},
                        "level": 6,
                        "installed": True,
                        "category": "communication",
                        "subtags": [],
                        "maintained": False,
                        "state": "working",
                    },
                },
                "categories": [
                    {
                        "id": "publishing",
                        "title": "Publication",
                        "description": "Site web, blog, wiki, CMS…",
                        "icon": "globe",
                        "subtags": [{"id": "website", "title": "Site web"}],
                    }
                ],
            },
        )
    )

    catalog = admin.get_app_catalog("fake-session-token")

    assert [a.name for a in catalog.apps] == ["Alpha", "Zebra"]
    assert catalog.apps[1].installed is True
    assert catalog.apps[1].maintained is False
    assert catalog.apps[0].category == "publishing"
    assert catalog.apps[0].subtags == ["website"]
    assert catalog.categories[0].id == "publishing"
    assert catalog.categories[0].subtags[0].title == "Site web"


@respx.mock
def test_get_app_catalog_rejects_invalid_session(admin_apps_catalog_url: str) -> None:
    respx.get(admin_apps_catalog_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_app_catalog("expired-token")


@pytest.fixture
def admin_apps_manifest_url(admin_apps_url: str) -> str:
    return f"{admin_apps_url}/manifest"


@respx.mock
def test_get_app_manifest_parses_install_fields(admin_apps_manifest_url: str) -> None:
    respx.get(admin_apps_manifest_url).mock(
        return_value=Response(
            200,
            json={
                "id": "roundcube",
                "name": "Roundcube",
                "description": "Webmail",
                "version": "1.7.2~ynh1",
                "install": [{"name": "domain", "type": "domain"}, {"name": "path", "type": "path"}],
            },
        )
    )

    manifest = admin.get_app_manifest("fake-session-token", "roundcube")

    assert manifest.id == "roundcube"
    assert len(manifest.install) == 2
    assert manifest.upstream.website is None


@respx.mock
def test_get_app_manifest_parses_upstream_links(admin_apps_manifest_url: str) -> None:
    respx.get(admin_apps_manifest_url).mock(
        return_value=Response(
            200,
            json={
                "id": "seafile",
                "name": "Seafile",
                "description": "Stockage cloud",
                "version": "13.0.25~ynh1",
                "install": [],
                "upstream": {
                    "license": "AGPL-3.0-or-later",
                    "website": "https://www.seafile.com",
                    "admindoc": "https://manual.seafile.com",
                    "userdoc": "https://manual.seafile.com",
                    "code": "https://github.com/haiwen/seafile",
                },
            },
        )
    )

    manifest = admin.get_app_manifest("fake-session-token", "seafile")

    assert manifest.upstream.license == "AGPL-3.0-or-later"
    assert manifest.upstream.website == "https://www.seafile.com"
    assert manifest.upstream.code == "https://github.com/haiwen/seafile"


@respx.mock
def test_get_app_manifest_picks_locale_for_dict_description(admin_apps_manifest_url: str) -> None:
    respx.get(admin_apps_manifest_url).mock(
        return_value=Response(
            200,
            json={
                "id": "nextcloud",
                "name": "Nextcloud",
                "description": {"en": "File sharing platform", "fr": "Plateforme de partage de fichiers"},
                "version": "28.0",
                "install": [],
            },
        )
    )

    manifest = admin.get_app_manifest("fake-session-token", "nextcloud")

    assert manifest.description == "Plateforme de partage de fichiers"


@respx.mock
def test_list_app_actions_returns_raw_payload(admin_apps_url: str) -> None:
    actions_url = f"{admin_apps_url}/roundcube/actions"
    respx.get(actions_url).mock(return_value=Response(200, json={"actions": [{"id": "test", "name": "Test"}]}))

    actions = admin.list_app_actions("fake-session-token", "roundcube")

    assert actions == {"actions": [{"id": "test", "name": "Test"}]}


@respx.mock
def test_run_app_action_calls_put(admin_apps_url: str) -> None:
    action_url = f"{admin_apps_url}/roundcube/actions/test"
    route = respx.put(action_url).mock(return_value=Response(200, json={}))

    admin.run_app_action("fake-session-token", "roundcube", "test", args="foo=bar")

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["app"] == "roundcube"
    assert body["action"] == "test"
    assert body["args"] == "foo=bar"


@respx.mock
def test_get_app_config_returns_raw_payload(admin_apps_url: str) -> None:
    config_url = f"{admin_apps_url}/roundcube/config"
    respx.get(config_url).mock(return_value=Response(200, json={"panels": []}))

    config = admin.get_app_config("fake-session-token", "roundcube")

    assert config == {"panels": []}


@respx.mock
def test_set_app_config_calls_put(admin_apps_url: str) -> None:
    config_url = f"{admin_apps_url}/roundcube/config/main"
    route = respx.put(config_url).mock(return_value=Response(200, json={}))

    admin.set_app_config("fake-session-token", "roundcube", "main", "with_sftp=1")

    assert route.called
    body = route.calls.last.request.content.decode()
    assert 'name="app"' not in body
    assert 'name="key"' not in body
    assert 'name="args"' in body and "with_sftp=1" in body


@respx.mock
def test_get_app_map_forwards_query_params(admin_apps_url: str) -> None:
    route = respx.get(f"{admin_apps_url}/map").mock(
        return_value=Response(200, json={"dev.byrtn.fr/actus": "grav"})
    )

    result = admin.get_app_map("fake-session-token", app_id="grav", raw=True, user="patrick.ritaine")

    assert result == {"dev.byrtn.fr/actus": "grav"}
    params = route.calls.last.request.url.params
    assert params["app"] == "grav"
    assert params["raw"] == ""
    assert params["user"] == "patrick.ritaine"


@respx.mock
def test_app_setting_get(admin_apps_url: str) -> None:
    route = respx.get(f"{admin_apps_url}/roundcube/settings").mock(return_value=Response(200, json="1"))

    result = admin.app_setting("fake-session-token", "roundcube", "some_key")

    assert result == {"value": "1"}
    assert route.calls.last.request.url.params["key"] == "some_key"
    assert "value" not in route.calls.last.request.url.params


@respx.mock
def test_app_setting_set(admin_apps_url: str) -> None:
    route = respx.get(f"{admin_apps_url}/roundcube/settings").mock(return_value=Response(200, json=None))

    admin.app_setting("fake-session-token", "roundcube", "some_key", value="new_value")

    params = route.calls.last.request.url.params
    assert params["key"] == "some_key"
    assert params["value"] == "new_value"


@respx.mock
def test_app_setting_delete(admin_apps_url: str) -> None:
    route = respx.get(f"{admin_apps_url}/roundcube/settings").mock(return_value=Response(200, json=None))

    admin.app_setting("fake-session-token", "roundcube", "some_key", delete=True)

    params = route.calls.last.request.url.params
    assert params["key"] == "some_key"
    assert params["delete"] == ""


@respx.mock
def test_app_makedefault_uses_native_path(admin_apps_url: str) -> None:
    route = respx.put(f"{admin_apps_url}/roundcube/default").mock(return_value=Response(200))

    admin.app_makedefault("fake-session-token", "roundcube", domain="dev.byrtn.fr", undo=False)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"app": "roundcube", "domain": "dev.byrtn.fr"}


@respx.mock
def test_get_app_shell_info_uses_short_timeout(admin_apps_url: str) -> None:
    route = respx.get(f"{admin_apps_url}/roundcube/shell").mock(return_value=Response(200, text="bash-5.1$"))

    result = admin.get_app_shell_info("fake-session-token", "roundcube")

    assert result == "bash-5.1$"
    assert route.called
