# Auteur : Patrick Ritaine

from __future__ import annotations

import csv
import io
from urllib.parse import parse_qs

from wappos_api.config import settings
from wappos_api.connectors import admin as admin_connector
from wappos_api.errors import ForbiddenError


def resolve_scope(session_token: str) -> list[str] | None:
    return admin_connector.resolve_caller_scope(session_token)


def domain_in_scope(domain: str, scope: list[str] | None) -> bool:
    if scope is None:
        return True
    return domain in scope or any(domain.endswith("." + owned) for owned in scope)


def require_domain_in_scope(domain: str, scope: list[str] | None) -> None:
    if not domain_in_scope(domain, scope):
        raise ForbiddenError(f"Domain {domain} is outside your scope")


def require_superadmin(scope: list[str] | None) -> None:
    if scope is not None:
        raise ForbiddenError("This action is reserved to the superadmin")


def filter_domains(domains: list[str], scope: list[str] | None) -> list[str]:
    if scope is None:
        return domains
    return [domain for domain in domains if domain_in_scope(domain, scope)]


def _domain_of(domain_path: str) -> str:
    return domain_path.split("/", 1)[0]


def filter_apps(apps: list, scope: list[str] | None) -> list:
    if scope is None:
        return apps
    return [app for app in apps if app.domain_path and domain_in_scope(_domain_of(app.domain_path), scope)]


def filter_app_map(app_map: dict, scope: list[str] | None, raw: bool) -> dict:
    if scope is None:
        return app_map
    if raw:
        return {key: value for key, value in app_map.items() if domain_in_scope(_domain_of(key), scope)}
    return {key: value for key, value in app_map.items() if domain_in_scope(key, scope)}


def resolve_app_domains(session_token: str, app_id: str) -> list[str]:
    raw_map = admin_connector.get_app_map(session_token, app_id=app_id, raw=True)
    return sorted({_domain_of(domain_path) for domain_path in raw_map})


def require_app_in_scope(session_token: str, app_id: str, scope: list[str] | None) -> None:
    if scope is None:
        return
    domains = resolve_app_domains(session_token, app_id)
    if not domains or not all(domain_in_scope(domain, scope) for domain in domains):
        raise ForbiddenError(f"App {app_id} is outside your scope")


def _domain_of_mail(mail: str) -> str:
    return mail.rsplit("@", 1)[-1] if "@" in mail else ""


def filter_users(users: list, scope: list[str] | None) -> list:
    if scope is None:
        return users
    return [user for user in users if domain_in_scope(_domain_of_mail(user.mail), scope)]


def require_user_in_scope(session_token: str, username: str, scope: list[str] | None) -> None:
    if scope is None:
        return
    user = admin_connector.get_user(session_token, username)
    if not domain_in_scope(_domain_of_mail(user.mail), scope):
        raise ForbiddenError(f"User {username} is outside your scope")


def resolve_permission_domain(session_token: str, permission: str) -> str | None:
    permissions = admin_connector.list_permissions(session_token)
    info = permissions.get(permission)
    if info is None or not info.url:
        return None
    return _domain_of(info.url)


def filter_permissions(permissions: dict, scope: list[str] | None) -> dict:
    if scope is None:
        return permissions
    return {
        name: info
        for name, info in permissions.items()
        if info.url and domain_in_scope(_domain_of(info.url), scope)
    }


def require_permission_in_scope(session_token: str, permission: str, scope: list[str] | None) -> None:
    if scope is None:
        return
    domain = resolve_permission_domain(session_token, permission)
    if domain is None or not domain_in_scope(domain, scope):
        raise ForbiddenError(f"Permission {permission} is outside your scope")


def require_usernames_in_scope(session_token: str, usernames: list[str] | None, scope: list[str] | None) -> None:
    if scope is None or not usernames:
        return
    for username in usernames:
        require_user_in_scope(session_token, username, scope)


_PROTECTED_GROUP_NAMES = {"admins", "all_users", "visitors"}
_OPEN_GROUP_NAMES = {"all_users", "visitors"}


def group_in_scope(session_token: str, groupname: str, scope: list[str] | None) -> bool:
    if scope is None:
        return True

    if groupname in _PROTECTED_GROUP_NAMES or groupname == settings.wappos_domain_admins_group:
        return False

    groups = admin_connector.list_groups_full(session_token)
    group = next((g for g in groups if g.name == groupname), None)
    if group is None:
        return False

    users = admin_connector.list_users(session_token)
    in_scope_usernames = {u.username for u in users if domain_in_scope(_domain_of_mail(u.mail), scope)}
    if not all(member in in_scope_usernames for member in group.members):
        return False

    for permission in group.permissions:
        domain = resolve_permission_domain(session_token, permission)
        if domain is None or not domain_in_scope(domain, scope):
            return False

    return True


def require_group_in_scope(session_token: str, groupname: str, scope: list[str] | None) -> None:
    if not group_in_scope(session_token, groupname, scope):
        raise ForbiddenError(f"Group {groupname} is outside your scope")


def require_new_group_name_allowed(groupname: str, scope: list[str] | None) -> None:
    if scope is None:
        return

    if groupname in _PROTECTED_GROUP_NAMES or groupname == settings.wappos_domain_admins_group:
        raise ForbiddenError(f"Group name {groupname} is reserved")


def filter_groups(session_token: str, groups: list, scope: list[str] | None) -> list:
    if scope is None:
        return groups
    return [g for g in groups if group_in_scope(session_token, g.name, scope)]


def require_permission_entries_in_scope(session_token: str, entries: list[str] | None, scope: list[str] | None) -> None:
    if scope is None or not entries:
        return
    groups = {g.name for g in admin_connector.list_groups_full(session_token)}
    for entry in entries:
        if entry in _OPEN_GROUP_NAMES:
            continue
        if entry in groups:
            require_group_in_scope(session_token, entry, scope)
        else:
            require_user_in_scope(session_token, entry, scope)


_FIREWALL_OWNER_PREFIX = "[wappos-owner:"
_FIREWALL_MIN_PORT_FOR_DOMAIN_ADMIN = 1024


def firewall_port_owner(comment: str) -> str | None:
    if not comment.startswith(_FIREWALL_OWNER_PREFIX):
        return None
    end = comment.find("]")
    if end == -1:
        return None
    return comment[len(_FIREWALL_OWNER_PREFIX):end]


def build_owned_firewall_comment(username: str, comment: str) -> str:
    label = f"{_FIREWALL_OWNER_PREFIX}{username}]"
    return f"{label} {comment}".strip() if comment else label


def require_firewall_port_open_allowed(port: int | str, scope: list[str] | None) -> None:
    if scope is None:
        return
    try:
        port_number = int(port)
    except ValueError:
        raise ForbiddenError(f"Invalid port {port}") from None
    if port_number < _FIREWALL_MIN_PORT_FOR_DOMAIN_ADMIN:
        raise ForbiddenError(f"Port {port} is reserved to the superadmin")


def require_firewall_port_owned_by(
    session_token: str, protocol: str, port: int | str, username: str, scope: list[str] | None
) -> None:
    if scope is None:
        return
    rules = admin_connector.list_firewall(session_token)
    ports = rules.tcp if protocol == "tcp" else rules.udp
    entry = next((p for p in ports if str(p.port) == str(port)), None)
    if entry is None or firewall_port_owner(entry.comment) != username:
        raise ForbiddenError(f"Port {port}/{protocol} is outside your scope")


def filter_firewall_rules(rules, username: str | None, scope: list[str] | None):
    if scope is None:
        return rules
    return type(rules)(
        tcp=[p for p in rules.tcp if firewall_port_owner(p.comment) == username],
        udp=[p for p in rules.udp if firewall_port_owner(p.comment) == username],
        upnp_enabled=rules.upnp_enabled,
    )


_TLS_PASSTHROUGH_FORCED_DESTINATION = "127.0.0.1"


def parse_tls_passthrough_entry(entry: str) -> tuple[str, str, str] | None:
    parts = entry.split(";")
    if len(parts) != 3:
        return None
    domain, destination, port = (part.strip() for part in parts)
    if not domain or not destination or not port:
        return None
    return domain, destination, port


def filter_tls_passthrough_entries(entries: list[str], scope: list[str] | None) -> list[str]:
    if scope is None:
        return entries
    kept = []
    for entry in entries:
        parsed = parse_tls_passthrough_entry(entry)
        if parsed is None:
            continue
        domain, _destination, _port = parsed
        if domain_in_scope(domain, scope):
            kept.append(entry)
    return kept


def require_tls_passthrough_entries_allowed(entries: list[str], scope: list[str] | None) -> None:
    if scope is None:
        return
    for entry in entries:
        parsed = parse_tls_passthrough_entry(entry)
        if parsed is None:
            raise ForbiddenError(f"Invalid TLS passthrough entry {entry}")
        domain, destination, _port = parsed
        if not domain_in_scope(domain, scope):
            raise ForbiddenError(f"Domain {domain} is outside your scope")
        if destination != _TLS_PASSTHROUGH_FORCED_DESTINATION:
            raise ForbiddenError(
                f"Destination {destination} is not allowed, domain admins may only target "
                f"{_TLS_PASSTHROUGH_FORCED_DESTINATION}"
            )


def merge_tls_passthrough_entries(
    existing_entries: list[str], submitted_entries: list[str], scope: list[str] | None
) -> list[str]:
    if scope is None:
        return submitted_entries
    require_tls_passthrough_entries_allowed(submitted_entries, scope)
    out_of_scope_entries = [
        entry
        for entry in existing_entries
        if (parsed := parse_tls_passthrough_entry(entry)) is None or not domain_in_scope(parsed[0], scope)
    ]
    return out_of_scope_entries + submitted_entries


def filter_users_csv(csv_text: str, scope: list[str] | None) -> str:
    if scope is None:
        return csv_text
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=";", quotechar='"')
    fieldnames = reader.fieldnames or []
    rows = [row for row in reader if domain_in_scope(_domain_of_mail(row.get("mail") or ""), scope)]
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames, delimiter=";", quotechar='"')
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().rstrip()


def resolve_backup_domains(session_token: str, name: str) -> list[str] | None:
    info = admin_connector.get_backup_info(session_token, name, with_details=True)
    if info.get("system"):
        return None
    apps = list(info.get("apps") or {})
    if not apps:
        return None
    domains: set[str] = set()
    for app_id in apps:
        domains.update(resolve_app_domains(session_token, app_id))
    return sorted(domains)


def backup_in_scope(session_token: str, name: str, scope: list[str] | None) -> bool:
    if scope is None:
        return True
    domains = resolve_backup_domains(session_token, name)
    if not domains:
        return False
    return all(domain_in_scope(domain, scope) for domain in domains)


def require_backup_in_scope(session_token: str, name: str, scope: list[str] | None) -> None:
    if not backup_in_scope(session_token, name, scope):
        raise ForbiddenError(f"Backup {name} is outside your scope")


def filter_backups(session_token: str, archives: dict, scope: list[str] | None) -> dict:
    if scope is None:
        return archives
    return {name: info for name, info in archives.items() if backup_in_scope(session_token, name, scope)}


def require_backup_params_allowed(
    session_token: str, system: list[str] | None, apps: list[str] | None, scope: list[str] | None
) -> None:
    if scope is None:
        return
    if system:
        raise ForbiddenError("System backups are reserved to the superadmin")
    for app_id in apps or []:
        require_app_in_scope(session_token, app_id, scope)


_SCOPABLE_DIAGNOSIS_CATEGORIES = {"dnsrecords", "web"}


def filter_diagnosis_categories(categories: list[str], scope: list[str] | None) -> list[str]:
    if scope is None:
        return categories
    return [c for c in categories if c in _SCOPABLE_DIAGNOSIS_CATEGORIES]


def require_diagnosis_category_allowed(category: str | None, scope: list[str] | None) -> None:
    if scope is None:
        return
    if category not in _SCOPABLE_DIAGNOSIS_CATEGORIES:
        raise ForbiddenError(f"Diagnosis category {category} is reserved to the superadmin")


def filter_diagnosis_reports(reports: list, scope: list[str] | None) -> list:
    if scope is None:
        return reports
    filtered = []
    for report in reports:
        if report.id not in _SCOPABLE_DIAGNOSIS_CATEGORIES:
            continue
        items = [item for item in report.items if domain_in_scope(item.meta.get("domain") or "", scope) and item.meta.get("domain")]
        report = report.model_copy(update={
            "items": items,
            "error_count": sum(1 for i in items if i.status == "ERROR" and not i.ignored),
            "warning_count": sum(1 for i in items if i.status == "WARNING" and not i.ignored),
            "ignored_count": sum(1 for i in items if i.ignored),
        })
        filtered.append(report)
    return filtered


def require_diagnosis_item_in_scope(meta: dict, scope: list[str] | None) -> None:
    if scope is None:
        return
    domain = meta.get("domain")
    if not domain or not domain_in_scope(domain, scope):
        raise ForbiddenError("This diagnosis item is outside your scope")


def resolve_owned_app_ids(session_token: str, scope: list[str] | None) -> set[str]:
    if scope is None:
        return set()
    raw_map = admin_connector.get_app_map(session_token, raw=True)
    owned: set[str] = set()
    for domain, paths in raw_map.items():
        if not domain_in_scope(domain, scope):
            continue
        for entry in paths.values():
            app_id = entry.get("id")
            if app_id:
                owned.add(app_id)
    return owned


def log_in_scope(name: str, scope: list[str] | None, owned_app_ids: set[str]) -> bool:
    if scope is None:
        return True
    if any(domain in name for domain in scope):
        return True
    tokens = set(name.split("-"))
    for app_id in owned_app_ids:
        if app_id in tokens or name.endswith(f"-{app_id}") or f"-{app_id}-" in name:
            return True
    return False


def filter_logs(session_token: str, entries: list, scope: list[str] | None) -> list:
    if scope is None:
        return entries
    owned_app_ids = resolve_owned_app_ids(session_token, scope)
    return [entry for entry in entries if log_in_scope(entry.name, scope, owned_app_ids)]


def require_log_in_scope(session_token: str, name: str, scope: list[str] | None) -> None:
    if scope is None:
        return
    owned_app_ids = resolve_owned_app_ids(session_token, scope)
    if not log_in_scope(name, scope, owned_app_ids):
        raise ForbiddenError(f"Log {name} is outside your scope")


def _manifest_has_domain_arg(install_options: list[dict]) -> bool:
    return any(option.get("id") == "domain" for option in install_options)


def require_install_allowed(
    session_token: str, app_id: str, args: str | None, scope: list[str] | None
) -> None:
    if scope is None:
        return
    manifest = admin_connector.get_app_manifest(session_token, app_id)
    if not _manifest_has_domain_arg(manifest.install):
        raise ForbiddenError(f"App {app_id} cannot be attributed to a domain, reserved to the superadmin")
    parsed = parse_qs(args or "")
    values = parsed.get("domain")
    domain = values[0] if values else None
    if not domain:
        raise ForbiddenError("A domain must be explicitly selected")
    require_domain_in_scope(domain, scope)


def require_cross_domain_change_allowed(
    session_token: str, app_id: str, domain: str, scope: list[str] | None
) -> None:
    if scope is None:
        return
    require_app_in_scope(session_token, app_id, scope)
    require_domain_in_scope(domain, scope)


def filter_cross_domain_list(domains: list[str], scope: list[str] | None) -> list[str]:
    if scope is None:
        return domains
    return [d for d in domains if domain_in_scope(d, scope)]
