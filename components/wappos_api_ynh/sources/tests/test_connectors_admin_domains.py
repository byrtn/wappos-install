from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest
import respx
from httpx import Response

from wappos_api.connectors import admin
from wappos_api.errors import InvalidCredentialsError, UpstreamProtocolError


@pytest.fixture
def admin_domains_url(admin_login_url: str) -> str:
    return admin_login_url.replace("/login", "/domains")


@respx.mock
def test_list_domain_names_parses_real_shape(admin_domains_url: str) -> None:
    respx.get(admin_domains_url).mock(
        return_value=Response(200, json={"domains": ["dev.byrtn.fr", "dev.wappos.fr"], "main": "dev.byrtn.fr"})
    )

    domains = admin.list_domain_names("fake-session-token")

    assert domains == ["dev.byrtn.fr", "dev.wappos.fr"]


@respx.mock
def test_list_domain_names_excludes_www_redirects(admin_domains_url: str) -> None:
    respx.get(admin_domains_url).mock(
        return_value=Response(
            200,
            json={
                "domains": ["dev.byrtn.fr", "www.dev.byrtn.fr", "dev.wappos.fr", "www.dev.wappos.fr"],
                "main": "dev.byrtn.fr",
            },
        )
    )

    domains = admin.list_domain_names("fake-session-token")

    assert domains == ["dev.byrtn.fr", "dev.wappos.fr"]


@respx.mock
def test_list_domain_names_rejects_invalid_session(admin_domains_url: str) -> None:
    respx.get(admin_domains_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.list_domain_names("expired-token")


@pytest.fixture
def admin_domain_url(admin_domains_url: str) -> str:
    return f"{admin_domains_url}/dev.byrtn.fr"


@respx.mock
def test_get_domain_detail_parses_real_shape(admin_domain_url: str) -> None:
    respx.get(admin_domain_url).mock(
        return_value=Response(
            200,
            json={
                "certificate": {
                    "CA_type": "letsencrypt",
                    "validity": 76,
                    "style": "success",
                    "summary": "letsencrypt",
                    "ACME_eligible": True,
                    "has_wildcards": True,
                },
                "registrar": "ovh",
                "apps": [{"id": "roundcube", "name": "Roundcube", "path": "/webmail"}],
                "main": True,
                "topest_parent": None,
            },
        )
    )

    detail = admin.get_domain_detail("fake-session-token", "dev.byrtn.fr")

    assert detail.name == "dev.byrtn.fr"
    assert detail.certificate.CA_type == "letsencrypt"
    assert detail.registrar == "ovh"
    assert detail.apps[0].id == "roundcube"
    assert detail.main is True


@respx.mock
def test_get_domain_detail_rejects_invalid_session(admin_domain_url: str) -> None:
    respx.get(admin_domain_url).mock(return_value=Response(401))

    with pytest.raises(InvalidCredentialsError):
        admin.get_domain_detail("expired-token", "dev.byrtn.fr")


@respx.mock
def test_get_domain_detail_malformed_apps_raises_protocol_error(admin_domain_url: str) -> None:
    respx.get(admin_domain_url).mock(
        return_value=Response(200, json={"apps": [{"name": "Sans id"}], "main": True})
    )

    with pytest.raises(UpstreamProtocolError):
        admin.get_domain_detail("fake-session-token", "dev.byrtn.fr")


@respx.mock
def test_get_domain_config_returns_raw_payload(admin_domain_url: str) -> None:
    respx.get(f"{admin_domain_url}/config").mock(return_value=Response(200, json={"panels": []}))

    config = admin.get_domain_config("fake-session-token", "dev.byrtn.fr")

    assert config == {"panels": []}


@respx.mock
def test_get_domain_dns_suggestion_returns_string(admin_domain_url: str) -> None:
    respx.get(f"{admin_domain_url}/dns/suggest").mock(return_value=Response(200, json="dev.byrtn.fr. IN A 1.2.3.4"))

    suggestion = admin.get_domain_dns_suggestion("fake-session-token", "dev.byrtn.fr")

    assert suggestion == "dev.byrtn.fr. IN A 1.2.3.4"


@respx.mock
def test_set_domain_config_calls_put(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/config/feature").mock(return_value=Response(200, json={}))

    admin.set_domain_config("fake-session-token", "dev.byrtn.fr", "feature", "mail_in=1&mail_out=1")

    assert route.called
    body = route.calls.last.request.content.decode()
    assert 'name="domain"' not in body
    assert 'name="args"' in body


@respx.mock
def test_set_domain_config_large_args_uses_multipart_not_json(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/config/feature").mock(return_value=Response(200, json={}))
    large_value = "a" * 200_000

    admin.set_domain_config("fake-session-token", "dev.byrtn.fr", "feature", f"portal_logo={large_value}")

    assert route.called
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert large_value.encode() in request.content


@respx.mock
def test_set_main_domain_calls_put(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/main").mock(return_value=Response(200))

    admin.set_main_domain("fake-session-token", "dev.byrtn.fr")

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content)["new_main_domain"] == "dev.byrtn.fr"


@respx.mock
def test_get_certificates_status_parses_real_shape(admin_domains_url: str) -> None:
    respx.get(f"{admin_domains_url}/*/cert").mock(
        return_value=Response(200, json={"certificates": {
            "dev.byrtn.fr": {"CA_type": "letsencrypt", "validity": 50, "style": "success", "summary": "letsencrypt"},
            "adguard.dev.byrtn.fr": {"CA_type": "selfsigned", "validity": 3649, "style": "warning", "summary": "selfsigned"},
        }})
    )

    certs = admin.get_certificates_status("fake-session-token")

    assert certs["dev.byrtn.fr"]["validity"] == 50
    assert certs["adguard.dev.byrtn.fr"]["style"] == "warning"


@respx.mock
def test_install_domain_certificate_calls_put_with_flags(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/cert").mock(return_value=Response(200))

    admin.install_domain_certificate("fake-session-token", "dev.byrtn.fr", force=True)

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["domain_list"] == ["dev.byrtn.fr"]
    assert body["force"] is True


@respx.mock
def test_renew_domain_certificate_calls_put(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/cert/renew").mock(return_value=Response(200))

    admin.renew_domain_certificate("fake-session-token", "dev.byrtn.fr")

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content)["domain_list"] == ["dev.byrtn.fr"]


@respx.mock
def test_install_domain_certificate_forwards_self_signed_and_no_checks(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/cert").mock(return_value=Response(200))

    admin.install_domain_certificate("fake-session-token", "dev.byrtn.fr", self_signed=True, no_checks=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["self_signed"] is True
    assert body["no_checks"] is True


@respx.mock
def test_renew_domain_certificate_forwards_email_and_no_checks(admin_domain_url: str) -> None:
    route = respx.put(f"{admin_domain_url}/cert/renew").mock(return_value=Response(200))

    admin.renew_domain_certificate("fake-session-token", "dev.byrtn.fr", email=True, no_checks=True)

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["email"] is True
    assert body["no_checks"] is True


@respx.mock
def test_add_domain_calls_post(admin_domains_url: str) -> None:
    route = respx.post(admin_domains_url).mock(return_value=Response(200))

    admin.add_domain("fake-session-token", "new.dev.byrtn.fr", install_letsencrypt_cert=True)

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["domain"] == "new.dev.byrtn.fr"
    assert body["install_letsencrypt_cert"] is True


@respx.mock
def test_remove_domain_calls_delete_with_domain_in_body(admin_domain_url: str) -> None:
    route = respx.delete(admin_domain_url).mock(return_value=Response(200))

    admin.remove_domain("fake-session-token", "dev.byrtn.fr", remove_apps=True)

    assert route.called
    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["domain"] == "dev.byrtn.fr"
    assert body["remove_apps"] is True
    assert body["force"] is True


@respx.mock
def test_remove_domain_forwards_dyndns_recovery_password(admin_domain_url: str) -> None:
    route = respx.delete(admin_domain_url).mock(return_value=Response(200))

    admin.remove_domain("fake-session-token", "dev.byrtn.fr", dyndns_recovery_password="secret123")

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body["dyndns_recovery_password"] == "secret123"


@respx.mock
def test_push_domain_dns_dry_run_uses_query_flag_and_body_domain(admin_domain_url: str) -> None:
    route = respx.post(f"{admin_domain_url}/dns/push", params={"dry_run": ""}).mock(
        return_value=Response(200, json={"create": [], "update": [], "delete": [], "unchanged": []})
    )

    result = admin.push_domain_dns("fake-session-token", "dev.byrtn.fr", dry_run=True)

    assert route.called
    import json as _json

    assert _json.loads(route.calls.last.request.content)["domain"] == "dev.byrtn.fr"
    assert result == {"create": [], "update": [], "delete": [], "unchanged": []}


@respx.mock
def test_push_domain_dns_real_push_uses_force_flag(admin_domain_url: str) -> None:
    route = respx.post(f"{admin_domain_url}/dns/push", params={"force": ""}).mock(return_value=Response(200, json={}))

    admin.push_domain_dns("fake-session-token", "dev.byrtn.fr", dry_run=False, force=True)

    assert route.called


@respx.mock
def test_check_domain_url_available(admin_login_url: str) -> None:
    url_available_url = admin_login_url.replace("/login", "/domain/dev.byrtn.fr/urlavailable")
    route = respx.get(url_available_url).mock(return_value=Response(200, json=True))

    result = admin.check_domain_url_available("fake-session-token", "dev.byrtn.fr", "/coffee")

    assert result is True
    assert route.calls.last.request.url.params["path"] == "/coffee"


@respx.mock
def test_run_domain_action_calls_put_with_body(admin_login_url: str) -> None:
    action_url = admin_login_url.replace("/login", "/domain/dev.byrtn.fr/actions/some_action")
    route = respx.put(action_url).mock(return_value=Response(200, json={}))

    admin.run_domain_action("fake-session-token", "dev.byrtn.fr", "some_action", args="foo=bar")

    import json as _json

    body = _json.loads(route.calls.last.request.content)
    assert body == {"domain": "dev.byrtn.fr", "action": "some_action", "args": "foo=bar"}
