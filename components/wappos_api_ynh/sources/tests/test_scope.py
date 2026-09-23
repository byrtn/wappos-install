from __future__ import annotations
# Auteur : Patrick Ritaine

import pytest

from wappos_api import scope
from wappos_api.errors import ForbiddenError, InvalidCredentialsError


def test_resolve_scope_returns_none_for_superadmin_token() -> None:
    assert scope.resolve_scope("real-yunohost-cookie") is None


def test_resolve_scope_returns_owned_domains_for_domain_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    from wappos_api.connectors import admin as admin_connector

    token = admin_connector._create_domain_admin_session("domain.admin")
    monkeypatch.setattr(
        "wappos_api.connectors.domain_owners.domains_owned_by", lambda username: ["dev.byrtn.fr"]
    )

    assert scope.resolve_scope(token) == ["dev.byrtn.fr"]


def test_resolve_scope_rejects_unknown_domain_admin_token() -> None:
    with pytest.raises(InvalidCredentialsError):
        scope.resolve_scope("da_unknown")


def test_domain_in_scope_true_when_unrestricted() -> None:
    assert scope.domain_in_scope("anything.example", None) is True


def test_domain_in_scope_true_for_owned_domain() -> None:
    assert scope.domain_in_scope("dev.byrtn.fr", ["dev.byrtn.fr"]) is True


def test_domain_in_scope_true_for_subdomain_of_owned_domain() -> None:
    assert scope.domain_in_scope("photography.dev.byrtn.fr", ["dev.byrtn.fr"]) is True


def test_domain_in_scope_false_for_unrelated_domain() -> None:
    assert scope.domain_in_scope("dev.wappos.fr", ["dev.byrtn.fr"]) is False


def test_require_domain_in_scope_raises_when_out_of_scope() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_domain_in_scope("dev.wappos.fr", ["dev.byrtn.fr"])


def test_require_domain_in_scope_passes_when_in_scope() -> None:
    scope.require_domain_in_scope("dev.byrtn.fr", ["dev.byrtn.fr"])


def test_require_superadmin_passes_for_none_scope() -> None:
    scope.require_superadmin(None)


def test_require_superadmin_raises_for_domain_admin_scope() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_superadmin(["dev.byrtn.fr"])


def test_filter_domains_returns_all_when_unrestricted() -> None:
    domains = ["dev.byrtn.fr", "dev.wappos.fr"]
    assert scope.filter_domains(domains, None) == domains


def test_filter_domains_keeps_only_owned_and_subdomains() -> None:
    domains = ["dev.byrtn.fr", "photography.dev.byrtn.fr", "dev.wappos.fr"]
    assert scope.filter_domains(domains, ["dev.byrtn.fr"]) == ["dev.byrtn.fr", "photography.dev.byrtn.fr"]


class _FakeApp:
    def __init__(self, domain_path: str | None) -> None:
        self.domain_path = domain_path


def test_filter_apps_returns_all_when_unrestricted() -> None:
    apps = [_FakeApp("dev.byrtn.fr/nextcloud"), _FakeApp(None)]
    assert scope.filter_apps(apps, None) == apps


def test_filter_apps_keeps_only_apps_in_scope() -> None:
    in_scope = _FakeApp("dev.byrtn.fr/nextcloud")
    out_of_scope = _FakeApp("dev.wappos.fr/grav")
    no_domain = _FakeApp(None)

    result = scope.filter_apps([in_scope, out_of_scope, no_domain], ["dev.byrtn.fr"])

    assert result == [in_scope]


def test_filter_app_map_raw_keeps_only_domains_in_scope() -> None:
    app_map = {
        "dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
        "dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}},
    }

    result = scope.filter_app_map(app_map, ["dev.byrtn.fr"], raw=True)

    assert result == {"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}}


def test_filter_app_map_non_raw_keeps_only_domains_in_scope() -> None:
    app_map = {"dev.byrtn.fr": {"actus": "grav"}, "dev.wappos.fr": {"webmail": "roundcube"}}

    result = scope.filter_app_map(app_map, ["dev.byrtn.fr"], raw=False)

    assert result == {"dev.byrtn.fr": {"actus": "grav"}}


def test_filter_app_map_returns_all_when_unrestricted() -> None:
    app_map = {"dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}}}
    assert scope.filter_app_map(app_map, None, raw=True) == app_map


def test_resolve_app_domains_extracts_unique_domains(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {
            "dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
            "photography.dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
        },
    )

    assert scope.resolve_app_domains("token", "grav") == ["dev.byrtn.fr", "photography.dev.byrtn.fr"]


def test_require_app_in_scope_passes_for_superadmin(monkeypatch: pytest.MonkeyPatch) -> None:
    scope.require_app_in_scope("token", "grav", None)


def test_require_app_in_scope_raises_when_app_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {"dev.wappos.fr": {"/x": {"label": "Grav", "id": "grav"}}},
    )

    with pytest.raises(ForbiddenError):
        scope.require_app_in_scope("token", "grav", ["dev.byrtn.fr"])


def test_require_app_in_scope_raises_when_app_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_app_map", lambda token, app_id=None, raw=False, user=None: {})

    with pytest.raises(ForbiddenError):
        scope.require_app_in_scope("token", "unknown-app", ["dev.byrtn.fr"])


def test_require_app_in_scope_passes_when_all_domains_owned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {
            "dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
            "photography.dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
        },
    )

    scope.require_app_in_scope("token", "grav", ["dev.byrtn.fr"])


class _FakeUser:
    def __init__(self, mail: str, username: str | None = None) -> None:
        self.mail = mail
        self.username = username or mail.split("@", 1)[0]


def test_filter_users_returns_all_when_unrestricted() -> None:
    users = [_FakeUser("patrick@dev.byrtn.fr")]
    assert scope.filter_users(users, None) == users


def test_filter_users_keeps_only_users_in_scope() -> None:
    in_scope = _FakeUser("patrick@dev.byrtn.fr")
    out_of_scope = _FakeUser("someone@dev.wappos.fr")

    assert scope.filter_users([in_scope, out_of_scope], ["dev.byrtn.fr"]) == [in_scope]


def test_require_user_in_scope_passes_for_superadmin() -> None:
    scope.require_user_in_scope("token", "patrick", None)


def test_require_user_in_scope_raises_when_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_user", lambda token, username: _FakeUser("someone@dev.wappos.fr"))

    with pytest.raises(ForbiddenError):
        scope.require_user_in_scope("token", "someone", ["dev.byrtn.fr"])


def test_require_user_in_scope_passes_when_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_user", lambda token, username: _FakeUser("patrick@dev.byrtn.fr"))

    scope.require_user_in_scope("token", "patrick", ["dev.byrtn.fr"])


def test_filter_users_csv_returns_all_when_unrestricted() -> None:
    csv_text = "username;mail\npatrick;patrick@dev.byrtn.fr"
    assert scope.filter_users_csv(csv_text, None) == csv_text


def test_filter_users_csv_keeps_only_rows_in_scope() -> None:
    csv_text = "username;mail\npatrick;patrick@dev.byrtn.fr\nsomeone;someone@dev.wappos.fr"

    result = scope.filter_users_csv(csv_text, ["dev.byrtn.fr"])

    assert "patrick@dev.byrtn.fr" in result
    assert "someone@dev.wappos.fr" not in result


class _FakePermissionInfo:
    def __init__(self, url: str | None) -> None:
        self.url = url


def test_resolve_permission_domain_returns_none_for_unknown_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_permissions", lambda token: {})

    assert scope.resolve_permission_domain("token", "unknown.main") is None


def test_resolve_permission_domain_returns_none_for_urlless_permission(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_permissions", lambda token: {"mail.main": _FakePermissionInfo(None)})

    assert scope.resolve_permission_domain("token", "mail.main") is None


def test_resolve_permission_domain_extracts_domain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "list_permissions",
        lambda token: {"roundcube.main": _FakePermissionInfo("dev.byrtn.fr/webmail")},
    )

    assert scope.resolve_permission_domain("token", "roundcube.main") == "dev.byrtn.fr"


def test_filter_permissions_returns_all_when_unrestricted() -> None:
    permissions = {"roundcube.main": _FakePermissionInfo("dev.byrtn.fr/webmail")}
    assert scope.filter_permissions(permissions, None) == permissions


def test_filter_permissions_excludes_urlless_and_out_of_scope() -> None:
    permissions = {
        "roundcube.main": _FakePermissionInfo("dev.byrtn.fr/webmail"),
        "grav.main": _FakePermissionInfo("dev.wappos.fr/actus"),
        "mail.main": _FakePermissionInfo(None),
    }

    result = scope.filter_permissions(permissions, ["dev.byrtn.fr"])

    assert list(result.keys()) == ["roundcube.main"]


def test_require_permission_in_scope_passes_for_superadmin() -> None:
    scope.require_permission_in_scope("token", "roundcube.main", None)


def test_require_permission_in_scope_raises_when_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "list_permissions",
        lambda token: {"grav.main": _FakePermissionInfo("dev.wappos.fr/actus")},
    )

    with pytest.raises(ForbiddenError):
        scope.require_permission_in_scope("token", "grav.main", ["dev.byrtn.fr"])


def test_require_permission_in_scope_passes_when_inside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "list_permissions",
        lambda token: {"roundcube.main": _FakePermissionInfo("dev.byrtn.fr/webmail")},
    )

    scope.require_permission_in_scope("token", "roundcube.main", ["dev.byrtn.fr"])


def test_require_usernames_in_scope_passes_for_superadmin() -> None:
    scope.require_usernames_in_scope("token", ["someone"], None)


def test_require_usernames_in_scope_passes_when_no_usernames() -> None:
    scope.require_usernames_in_scope("token", None, ["dev.byrtn.fr"])


def test_require_usernames_in_scope_raises_when_one_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_user", lambda token, username: _FakeUser(f"{username}@dev.wappos.fr"))

    with pytest.raises(ForbiddenError):
        scope.require_usernames_in_scope("token", ["someone"], ["dev.byrtn.fr"])


class _FakeGroup:
    def __init__(self, name: str, members: list[str], permissions: list[str]) -> None:
        self.name = name
        self.members = members
        self.permissions = permissions


def test_group_in_scope_true_for_superadmin() -> None:
    assert scope.group_in_scope("token", "team", None) is True


def test_group_in_scope_false_for_protected_group_names(monkeypatch: pytest.MonkeyPatch) -> None:
    assert scope.group_in_scope("token", "admins", ["dev.byrtn.fr"]) is False
    assert scope.group_in_scope("token", "all_users", ["dev.byrtn.fr"]) is False
    assert scope.group_in_scope("token", "visitors", ["dev.byrtn.fr"]) is False


def test_group_in_scope_false_for_domain_admins_system_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.settings, "wappos_domain_admins_group", "wappos_domain_admins")

    assert scope.group_in_scope("token", "wappos_domain_admins", ["dev.byrtn.fr"]) is False


def test_group_in_scope_false_for_unknown_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_groups_full", lambda token: [])

    assert scope.group_in_scope("token", "team", ["dev.byrtn.fr"]) is False


def test_group_in_scope_false_when_member_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "list_groups_full", lambda token: [_FakeGroup("team", ["someone"], [])]
    )
    monkeypatch.setattr(scope.admin_connector, "list_users", lambda token: [_FakeUser("someone@dev.wappos.fr")])

    assert scope.group_in_scope("token", "team", ["dev.byrtn.fr"]) is False


def test_group_in_scope_false_when_permission_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "list_groups_full", lambda token: [_FakeGroup("team", [], ["grav.main"])]
    )
    monkeypatch.setattr(scope.admin_connector, "list_users", lambda token: [])
    monkeypatch.setattr(
        scope.admin_connector, "list_permissions", lambda token: {"grav.main": _FakePermissionInfo("dev.wappos.fr/actus")}
    )

    assert scope.group_in_scope("token", "team", ["dev.byrtn.fr"]) is False


def test_group_in_scope_true_when_members_and_permissions_all_in_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "list_groups_full", lambda token: [_FakeGroup("team", ["patrick"], ["roundcube.main"])]
    )
    monkeypatch.setattr(scope.admin_connector, "list_users", lambda token: [_FakeUser("patrick@dev.byrtn.fr")])
    monkeypatch.setattr(
        scope.admin_connector,
        "list_permissions",
        lambda token: {"roundcube.main": _FakePermissionInfo("dev.byrtn.fr/webmail")},
    )

    assert scope.group_in_scope("token", "team", ["dev.byrtn.fr"]) is True


def test_require_group_in_scope_raises_when_out_of_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ForbiddenError):
        scope.require_group_in_scope("token", "admins", ["dev.byrtn.fr"])


def test_require_new_group_name_allowed_passes_for_superadmin() -> None:
    scope.require_new_group_name_allowed("admins", None)


def test_require_new_group_name_allowed_raises_for_reserved_name() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_new_group_name_allowed("all_users", ["dev.byrtn.fr"])


def test_require_new_group_name_allowed_passes_for_custom_name() -> None:
    scope.require_new_group_name_allowed("team", ["dev.byrtn.fr"])


def test_filter_groups_returns_all_when_unrestricted() -> None:
    groups = [_FakeGroup("team", [], [])]
    assert scope.filter_groups("token", groups, None) == groups


def test_filter_groups_excludes_out_of_scope_groups(monkeypatch: pytest.MonkeyPatch) -> None:
    in_scope = _FakeGroup("team", ["patrick"], [])
    out_of_scope = _FakeGroup("admins", [], [])
    monkeypatch.setattr(scope.admin_connector, "list_groups_full", lambda token: [in_scope, out_of_scope])
    monkeypatch.setattr(scope.admin_connector, "list_users", lambda token: [_FakeUser("patrick@dev.byrtn.fr")])

    assert scope.filter_groups("token", [in_scope, out_of_scope], ["dev.byrtn.fr"]) == [in_scope]


def test_require_permission_entries_in_scope_passes_for_superadmin() -> None:
    scope.require_permission_entries_in_scope("token", ["someone"], None)


def test_require_permission_entries_in_scope_skips_open_groups(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_groups_full", lambda token: [])

    scope.require_permission_entries_in_scope("token", ["all_users", "visitors"], ["dev.byrtn.fr"])


def test_require_permission_entries_in_scope_checks_custom_group(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_groups_full", lambda token: [_FakeGroup("admins", [], [])])

    with pytest.raises(ForbiddenError):
        scope.require_permission_entries_in_scope("token", ["admins"], ["dev.byrtn.fr"])


def test_require_permission_entries_in_scope_checks_username(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "list_groups_full", lambda token: [])
    monkeypatch.setattr(scope.admin_connector, "get_user", lambda token, username: _FakeUser(f"{username}@dev.wappos.fr"))

    with pytest.raises(ForbiddenError):
        scope.require_permission_entries_in_scope("token", ["someone"], ["dev.byrtn.fr"])


class _FakePort:
    def __init__(self, port: int, comment: str) -> None:
        self.port = port
        self.comment = comment


class _FakeFirewallRules:
    def __init__(self, tcp: list, udp: list, upnp_enabled: bool = False) -> None:
        self.tcp = tcp
        self.udp = udp
        self.upnp_enabled = upnp_enabled


def test_firewall_port_owner_returns_none_for_unowned_comment() -> None:
    assert scope.firewall_port_owner("SMTP email server (postfix)") is None


def test_firewall_port_owner_extracts_username() -> None:
    assert scope.firewall_port_owner("[wappos-owner:patrick] my app") == "patrick"


def test_build_owned_firewall_comment_prefixes_label() -> None:
    assert scope.build_owned_firewall_comment("patrick", "my app") == "[wappos-owner:patrick] my app"


def test_build_owned_firewall_comment_without_comment() -> None:
    assert scope.build_owned_firewall_comment("patrick", "") == "[wappos-owner:patrick]"


def test_require_firewall_port_open_allowed_passes_for_superadmin() -> None:
    scope.require_firewall_port_open_allowed("80", None)


def test_require_firewall_port_open_allowed_raises_for_privileged_port() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_firewall_port_open_allowed("80", ["dev.byrtn.fr"])


def test_require_firewall_port_open_allowed_passes_for_unprivileged_port() -> None:
    scope.require_firewall_port_open_allowed("8080", ["dev.byrtn.fr"])


def test_require_firewall_port_open_allowed_raises_for_invalid_port() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_firewall_port_open_allowed("not-a-port", ["dev.byrtn.fr"])


def test_require_firewall_port_owned_by_passes_for_superadmin() -> None:
    scope.require_firewall_port_owned_by("token", "tcp", "8080", "patrick", None)


def test_require_firewall_port_owned_by_raises_when_not_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = _FakeFirewallRules(tcp=[_FakePort(8080, "[wappos-owner:other] app")], udp=[])
    monkeypatch.setattr(scope.admin_connector, "list_firewall", lambda token: rules)

    with pytest.raises(ForbiddenError):
        scope.require_firewall_port_owned_by("token", "tcp", "8080", "patrick", ["dev.byrtn.fr"])


def test_require_firewall_port_owned_by_passes_when_owner(monkeypatch: pytest.MonkeyPatch) -> None:
    rules = _FakeFirewallRules(tcp=[_FakePort(8080, "[wappos-owner:patrick] app")], udp=[])
    monkeypatch.setattr(scope.admin_connector, "list_firewall", lambda token: rules)

    scope.require_firewall_port_owned_by("token", "tcp", "8080", "patrick", ["dev.byrtn.fr"])


def test_filter_firewall_rules_returns_all_when_unrestricted() -> None:
    rules = _FakeFirewallRules(tcp=[_FakePort(8080, "anything")], udp=[])
    assert scope.filter_firewall_rules(rules, "patrick", None) is rules


def test_filter_firewall_rules_keeps_only_owned_ports() -> None:
    owned = _FakePort(8080, "[wappos-owner:patrick] app")
    other = _FakePort(9090, "[wappos-owner:other] app")
    unowned = _FakePort(80, "SMTP email server")
    rules = _FakeFirewallRules(tcp=[owned, other, unowned], udp=[])

    result = scope.filter_firewall_rules(rules, "patrick", ["dev.byrtn.fr"])

    assert result.tcp == [owned]
    assert result.udp == []


def test_parse_tls_passthrough_entry_returns_none_for_malformed_entry() -> None:
    assert scope.parse_tls_passthrough_entry("dev.byrtn.fr;192.168.1.42") is None


def test_parse_tls_passthrough_entry_extracts_fields() -> None:
    assert scope.parse_tls_passthrough_entry("dev.byrtn.fr;192.168.1.42;443") == (
        "dev.byrtn.fr", "192.168.1.42", "443"
    )


def test_filter_tls_passthrough_entries_returns_all_when_unrestricted() -> None:
    entries = ["dev.byrtn.fr;127.0.0.1;443"]
    assert scope.filter_tls_passthrough_entries(entries, None) == entries


def test_filter_tls_passthrough_entries_keeps_only_owned_domains() -> None:
    entries = ["dev.byrtn.fr;127.0.0.1;443", "dev.wappos.fr;127.0.0.1;443"]

    assert scope.filter_tls_passthrough_entries(entries, ["dev.byrtn.fr"]) == ["dev.byrtn.fr;127.0.0.1;443"]


def test_require_tls_passthrough_entries_allowed_passes_for_superadmin() -> None:
    scope.require_tls_passthrough_entries_allowed(["dev.byrtn.fr;192.168.1.42;443"], None)


def test_require_tls_passthrough_entries_allowed_raises_for_out_of_scope_domain() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_tls_passthrough_entries_allowed(["dev.wappos.fr;127.0.0.1;443"], ["dev.byrtn.fr"])


def test_require_tls_passthrough_entries_allowed_raises_for_non_local_destination() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_tls_passthrough_entries_allowed(["dev.byrtn.fr;192.168.1.42;443"], ["dev.byrtn.fr"])


def test_require_tls_passthrough_entries_allowed_passes_for_local_destination() -> None:
    scope.require_tls_passthrough_entries_allowed(["dev.byrtn.fr;127.0.0.1;443"], ["dev.byrtn.fr"])


def test_require_tls_passthrough_entries_allowed_raises_for_malformed_entry() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_tls_passthrough_entries_allowed(["not-a-valid-entry"], ["dev.byrtn.fr"])


def test_merge_tls_passthrough_entries_returns_submitted_when_unrestricted() -> None:
    submitted = ["dev.byrtn.fr;192.168.1.42;443"]
    assert scope.merge_tls_passthrough_entries([], submitted, None) == submitted


def test_merge_tls_passthrough_entries_keeps_out_of_scope_entries_and_adds_submitted() -> None:
    existing = ["dev.wappos.fr;192.168.1.1;443"]
    submitted = ["dev.byrtn.fr;127.0.0.1;443"]

    result = scope.merge_tls_passthrough_entries(existing, submitted, ["dev.byrtn.fr"])

    assert result == ["dev.wappos.fr;192.168.1.1;443", "dev.byrtn.fr;127.0.0.1;443"]


def test_merge_tls_passthrough_entries_raises_for_disallowed_submission() -> None:
    with pytest.raises(ForbiddenError):
        scope.merge_tls_passthrough_entries([], ["dev.wappos.fr;127.0.0.1;443"], ["dev.byrtn.fr"])


def test_resolve_backup_domains_returns_none_for_system_backup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_backup_info", lambda token, name, with_details=True: {"system": {"conf_nginx": {}}, "apps": {}})

    assert scope.resolve_backup_domains("token", "daily") is None


def test_resolve_backup_domains_returns_none_for_empty_backup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_backup_info", lambda token, name, with_details=True: {"system": {}, "apps": {}})

    assert scope.resolve_backup_domains("token", "daily") is None


def test_resolve_backup_domains_returns_domains_of_apps(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_backup_info", lambda token, name, with_details=True: {"system": {}, "apps": {"grav": {}}}
    )
    monkeypatch.setattr(scope, "resolve_app_domains", lambda token, app_id: ["dev.byrtn.fr"])

    assert scope.resolve_backup_domains("token", "daily") == ["dev.byrtn.fr"]


def test_backup_in_scope_true_for_superadmin() -> None:
    assert scope.backup_in_scope("token", "daily", None) is True


def test_backup_in_scope_false_for_system_backup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_backup_domains", lambda token, name: None)

    assert scope.backup_in_scope("token", "daily", ["dev.byrtn.fr"]) is False


def test_backup_in_scope_false_when_a_domain_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_backup_domains", lambda token, name: ["dev.byrtn.fr", "dev.wappos.fr"])

    assert scope.backup_in_scope("token", "daily", ["dev.byrtn.fr"]) is False


def test_backup_in_scope_true_when_all_domains_owned(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_backup_domains", lambda token, name: ["dev.byrtn.fr"])

    assert scope.backup_in_scope("token", "daily", ["dev.byrtn.fr"]) is True


def test_require_backup_in_scope_raises_when_out_of_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_backup_domains", lambda token, name: None)

    with pytest.raises(ForbiddenError):
        scope.require_backup_in_scope("token", "daily", ["dev.byrtn.fr"])


def test_filter_backups_returns_all_when_unrestricted() -> None:
    archives = {"daily": {}, "weekly": {}}
    assert scope.filter_backups("token", archives, None) == archives


def test_filter_backups_keeps_only_owned_archives(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_resolve(token, name):
        return ["dev.byrtn.fr"] if name == "daily" else None

    monkeypatch.setattr(scope, "resolve_backup_domains", fake_resolve)
    archives = {"daily": {"size": 1}, "system-only": {"size": 2}}

    assert scope.filter_backups("token", archives, ["dev.byrtn.fr"]) == {"daily": {"size": 1}}


def test_require_backup_params_allowed_passes_for_superadmin() -> None:
    scope.require_backup_params_allowed("token", ["conf_nginx"], ["grav"], None)


def test_require_backup_params_allowed_raises_for_system(monkeypatch: pytest.MonkeyPatch) -> None:
    with pytest.raises(ForbiddenError):
        scope.require_backup_params_allowed("token", ["conf_nginx"], None, ["dev.byrtn.fr"])


def test_require_backup_params_allowed_checks_app_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_map", lambda token, app_id=None, raw=False, user=None: {"dev.wappos.fr": {"/x": {}}}
    )

    with pytest.raises(ForbiddenError):
        scope.require_backup_params_allowed("token", None, ["grav"], ["dev.byrtn.fr"])


def test_require_backup_params_allowed_passes_when_apps_in_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_map", lambda token, app_id=None, raw=False, user=None: {"dev.byrtn.fr": {"/x": {}}}
    )

    scope.require_backup_params_allowed("token", None, ["grav"], ["dev.byrtn.fr"])


def test_filter_diagnosis_categories_returns_all_when_unrestricted() -> None:
    categories = ["dnsrecords", "web", "mail", "ip"]
    assert scope.filter_diagnosis_categories(categories, None) == categories


def test_filter_diagnosis_categories_keeps_only_scopable() -> None:
    categories = ["dnsrecords", "web", "mail", "ip"]
    assert scope.filter_diagnosis_categories(categories, ["dev.byrtn.fr"]) == ["dnsrecords", "web"]


def test_require_diagnosis_category_allowed_passes_for_superadmin() -> None:
    scope.require_diagnosis_category_allowed(None, None)
    scope.require_diagnosis_category_allowed("mail", None)


def test_require_diagnosis_category_allowed_raises_for_non_scopable() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_diagnosis_category_allowed("mail", ["dev.byrtn.fr"])


def test_require_diagnosis_category_allowed_raises_for_none_category() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_diagnosis_category_allowed(None, ["dev.byrtn.fr"])


def test_require_diagnosis_category_allowed_passes_for_scopable() -> None:
    scope.require_diagnosis_category_allowed("dnsrecords", ["dev.byrtn.fr"])


class _FakeDiagnosisItem:
    def __init__(self, status: str, meta: dict, ignored: bool = False) -> None:
        self.status = status
        self.meta = meta
        self.ignored = ignored


class _FakeDiagnosisReport:
    def __init__(self, report_id: str, items: list) -> None:
        self.id = report_id
        self.items = items
        self.error_count = 0
        self.warning_count = 0
        self.ignored_count = 0

    def model_copy(self, update: dict):
        merged = {"id": self.id, "items": self.items, "error_count": 0, "warning_count": 0, "ignored_count": 0}
        merged.update(update)
        result = _FakeDiagnosisReport(merged["id"], merged["items"])
        result.error_count = merged["error_count"]
        result.warning_count = merged["warning_count"]
        result.ignored_count = merged["ignored_count"]
        return result


def test_filter_diagnosis_reports_returns_all_when_unrestricted() -> None:
    reports = [_FakeDiagnosisReport("mail", [])]
    assert scope.filter_diagnosis_reports(reports, None) == reports


def test_filter_diagnosis_reports_excludes_non_scopable_category() -> None:
    reports = [_FakeDiagnosisReport("mail", [_FakeDiagnosisItem("ERROR", {})])]

    assert scope.filter_diagnosis_reports(reports, ["dev.byrtn.fr"]) == []


def test_filter_diagnosis_reports_keeps_only_items_in_scope() -> None:
    in_scope_item = _FakeDiagnosisItem("ERROR", {"domain": "dev.byrtn.fr"})
    out_of_scope_item = _FakeDiagnosisItem("WARNING", {"domain": "dev.wappos.fr"})
    no_domain_item = _FakeDiagnosisItem("ERROR", {})
    reports = [_FakeDiagnosisReport("web", [in_scope_item, out_of_scope_item, no_domain_item])]

    result = scope.filter_diagnosis_reports(reports, ["dev.byrtn.fr"])

    assert len(result) == 1
    assert result[0].items == [in_scope_item]
    assert result[0].error_count == 1
    assert result[0].warning_count == 0


def test_require_diagnosis_item_in_scope_passes_for_superadmin() -> None:
    scope.require_diagnosis_item_in_scope({}, None)


def test_require_diagnosis_item_in_scope_raises_without_domain() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_diagnosis_item_in_scope({}, ["dev.byrtn.fr"])


def test_require_diagnosis_item_in_scope_raises_for_out_of_scope_domain() -> None:
    with pytest.raises(ForbiddenError):
        scope.require_diagnosis_item_in_scope({"domain": "dev.wappos.fr"}, ["dev.byrtn.fr"])


def test_require_diagnosis_item_in_scope_passes_for_owned_domain() -> None:
    scope.require_diagnosis_item_in_scope({"domain": "dev.byrtn.fr"}, ["dev.byrtn.fr"])


def test_resolve_owned_app_ids_returns_empty_for_superadmin() -> None:
    assert scope.resolve_owned_app_ids("token", None) == set()


def test_resolve_owned_app_ids_keeps_only_owned_domains(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector,
        "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {
            "dev.byrtn.fr": {"/actus": {"label": "Grav", "id": "grav"}},
            "dev.wappos.fr": {"/webmail": {"label": "Roundcube", "id": "roundcube"}},
        },
    )

    assert scope.resolve_owned_app_ids("token", ["dev.byrtn.fr"]) == {"grav"}


def test_log_in_scope_true_for_superadmin() -> None:
    assert scope.log_in_scope("app_install-grav", None, set()) is True


def test_log_in_scope_true_for_domain_substring_match() -> None:
    assert scope.log_in_scope("domain_cert_install-dev.byrtn.fr", ["dev.byrtn.fr"], set()) is True


def test_log_in_scope_false_for_unrelated_domain() -> None:
    assert scope.log_in_scope("domain_cert_install-dev.wappos.fr", ["dev.byrtn.fr"], set()) is False


def test_log_in_scope_true_for_owned_app_token() -> None:
    assert scope.log_in_scope("app_install-grav", ["dev.byrtn.fr"], {"grav"}) is True


def test_log_in_scope_false_for_unowned_app() -> None:
    assert scope.log_in_scope("app_install-roundcube", ["dev.byrtn.fr"], {"grav"}) is False


def test_filter_logs_returns_all_when_unrestricted() -> None:
    class _FakeLogEntry:
        def __init__(self, name: str) -> None:
            self.name = name

    entries = [_FakeLogEntry("settings_set")]
    assert scope.filter_logs("token", entries, None) == entries


def test_filter_logs_keeps_only_matching_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    class _FakeLogEntry:
        def __init__(self, name: str) -> None:
            self.name = name

    monkeypatch.setattr(scope, "resolve_owned_app_ids", lambda token, scope_arg: set())
    owned = _FakeLogEntry("domain_cert_install-dev.byrtn.fr")
    unrelated = _FakeLogEntry("settings_set")
    entries = [owned, unrelated]

    assert scope.filter_logs("token", entries, ["dev.byrtn.fr"]) == [owned]


def test_require_log_in_scope_passes_for_superadmin() -> None:
    scope.require_log_in_scope("token", "settings_set", None)


def test_require_log_in_scope_raises_when_out_of_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_owned_app_ids", lambda token, scope_arg: set())

    with pytest.raises(ForbiddenError):
        scope.require_log_in_scope("token", "settings_set", ["dev.byrtn.fr"])


def test_require_log_in_scope_passes_when_in_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope, "resolve_owned_app_ids", lambda token, scope_arg: set())

    scope.require_log_in_scope("token", "domain_cert_install-dev.byrtn.fr", ["dev.byrtn.fr"])


class _FakeManifest:
    def __init__(self, install: list) -> None:
        self.install = install


def test_require_install_allowed_passes_for_superadmin() -> None:
    scope.require_install_allowed("token", "grav", "domain=dev.byrtn.fr", None)


def test_require_install_allowed_raises_when_no_domain_arg_in_manifest(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(scope.admin_connector, "get_app_manifest", lambda token, app_id: _FakeManifest([]))

    with pytest.raises(ForbiddenError):
        scope.require_install_allowed("token", "some_system_tool", "domain=dev.byrtn.fr", ["dev.byrtn.fr"])


def test_require_install_allowed_raises_when_domain_missing_from_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_manifest", lambda token, app_id: _FakeManifest([{"id": "domain"}])
    )

    with pytest.raises(ForbiddenError):
        scope.require_install_allowed("token", "grav", "path=/actus", ["dev.byrtn.fr"])


def test_require_install_allowed_raises_when_domain_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_manifest", lambda token, app_id: _FakeManifest([{"id": "domain"}])
    )

    with pytest.raises(ForbiddenError):
        scope.require_install_allowed("token", "grav", "domain=dev.wappos.fr", ["dev.byrtn.fr"])


def test_require_install_allowed_passes_when_domain_in_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_manifest", lambda token, app_id: _FakeManifest([{"id": "domain"}])
    )

    scope.require_install_allowed("token", "grav", "domain=dev.byrtn.fr&path=/actus", ["dev.byrtn.fr"])


def test_require_cross_domain_change_allowed_passes_for_superadmin() -> None:
    scope.require_cross_domain_change_allowed("token", "grav", "dev.byrtn.fr", None)


def test_require_cross_domain_change_allowed_raises_when_app_outside_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {"dev.wappos.fr": {"/x": {"label": "Grav", "id": "grav"}}},
    )

    with pytest.raises(ForbiddenError):
        scope.require_cross_domain_change_allowed("token", "grav", "dev.byrtn.fr", ["dev.byrtn.fr"])


def test_require_cross_domain_change_allowed_raises_when_target_domain_outside_scope(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {"dev.byrtn.fr": {"/x": {"label": "Grav", "id": "grav"}}},
    )

    with pytest.raises(ForbiddenError):
        scope.require_cross_domain_change_allowed("token", "grav", "dev.wappos.fr", ["dev.byrtn.fr"])


def test_require_cross_domain_change_allowed_passes_when_both_in_scope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scope.admin_connector, "get_app_map",
        lambda token, app_id=None, raw=False, user=None: {"dev.byrtn.fr": {"/x": {"label": "Grav", "id": "grav"}}},
    )

    scope.require_cross_domain_change_allowed("token", "grav", "dev.byrtn.fr", ["dev.byrtn.fr"])


def test_filter_cross_domain_list_returns_all_when_unrestricted() -> None:
    domains = ["dev.byrtn.fr", "dev.wappos.fr"]
    assert scope.filter_cross_domain_list(domains, None) == domains


def test_filter_cross_domain_list_keeps_only_owned() -> None:
    domains = ["dev.byrtn.fr", "dev.wappos.fr"]
    assert scope.filter_cross_domain_list(domains, ["dev.byrtn.fr"]) == ["dev.byrtn.fr"]
