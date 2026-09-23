#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import json
import re
import subprocess
import sys
from pathlib import Path

_REGISTRY_PATH = Path("/etc/yunohost/wappos_domain_smtp_relay.json")
_RELAYHOST_MAP_PATH = Path("/etc/postfix/wappos_sender_relayhost_maps")
_SASL_PASSWD_PATH = Path("/etc/postfix/wappos_sasl_passwd")
_MAIN_CF_PATH = Path("/etc/postfix/main.cf")
_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")

_MAIN_CF_DIRECTIVES = {
    "sender_dependent_relayhost_maps": f"hash:{_RELAYHOST_MAP_PATH}",
    "smtp_sender_dependent_authentication": "yes",
    "smtp_sasl_password_maps": f"hash:{_SASL_PASSWD_PATH}",
    "smtp_sasl_auth_enable": "yes",
    "smtp_sasl_security_options": "noanonymous",
}


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=30)


def _load_registry() -> dict:
    if not _REGISTRY_PATH.exists():
        return {}
    return json.loads(_REGISTRY_PATH.read_text())


def _save_registry(data: dict) -> None:
    _REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))
    _REGISTRY_PATH.chmod(0o600)


def _all_domains() -> list[str]:
    result = _run("yunohost", "domain", "list", "--output-as", "json")
    return json.loads(result.stdout)["domains"]


def _validate_domain(domain: str) -> str:
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f"Domaine invalide : {domain!r}")
    if domain not in _all_domains():
        raise ValueError(f"Domaine inconnu : {domain!r}")
    return domain


def _validate_port(port: str) -> int:
    try:
        port_number = int(port)
    except ValueError:
        raise ValueError(f"Port invalide : {port!r}") from None
    if not (1 <= port_number <= 65535):
        raise ValueError(f"Port hors plage : {port_number!r}")
    return port_number


def _ensure_main_cf() -> None:
    content = _MAIN_CF_PATH.read_text()
    changed = False
    for key, value in _MAIN_CF_DIRECTIVES.items():
        pattern = re.compile(rf"^{re.escape(key)}\s*=.*$", re.MULTILINE)
        line = f"{key} = {value}"
        if pattern.search(content):
            if not re.search(rf"^{re.escape(line)}$", content, re.MULTILINE):
                content = pattern.sub(line, content)
                changed = True
        else:
            content = content.rstrip("\n") + f"\n{line}\n"
            changed = True
    if changed:
        _MAIN_CF_PATH.write_text(content)


def _regenerate_maps() -> None:
    registry = _load_registry()

    relayhost_lines = []
    sasl_lines = []
    for domain, entry in sorted(registry.items()):
        host = entry["host"]
        port = entry["port"]
        relayhost_lines.append(f"@{domain} [{host}]:{port}")
        if entry.get("user") and entry.get("password"):
            sasl_lines.append(f"@{domain} {entry['user']}:{entry['password']}")

    _RELAYHOST_MAP_PATH.write_text("\n".join(relayhost_lines) + ("\n" if relayhost_lines else ""))
    _SASL_PASSWD_PATH.write_text("\n".join(sasl_lines) + ("\n" if sasl_lines else ""))
    _SASL_PASSWD_PATH.chmod(0o600)

    _run("postmap", str(_RELAYHOST_MAP_PATH))
    _run("postmap", str(_SASL_PASSWD_PATH))
    _run("postfix", "check")
    _run("systemctl", "reload", "postfix")


def set_relay(domain: str, host: str, port: str, user: str, password: str) -> None:
    _validate_domain(domain)
    port_number = _validate_port(port)
    if not host:
        raise ValueError("Hôte de relais requis")

    _ensure_main_cf()

    registry = _load_registry()
    existing = registry.get(domain)
    if not password and existing:
        password = existing.get("password", "")
    registry[domain] = {"host": host, "port": port_number, "user": user, "password": password}
    _save_registry(registry)
    _regenerate_maps()


def remove_relay(domain: str) -> None:
    _validate_domain(domain)
    registry = _load_registry()
    if domain not in registry:
        return
    registry.pop(domain)
    _save_registry(registry)
    _regenerate_maps()


def get_relay(domain: str) -> dict | None:
    _validate_domain(domain)
    entry = _load_registry().get(domain)
    if entry is None:
        return None
    return {"host": entry["host"], "port": entry["port"], "user": entry.get("user") or "", "has_password": bool(entry.get("password"))}


def ensure_infrastructure() -> None:
    _ensure_main_cf()
    if not _RELAYHOST_MAP_PATH.exists() or not _SASL_PASSWD_PATH.exists():
        _regenerate_maps()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if action == "set" and len(sys.argv) == 7:
            set_relay(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        elif action == "remove" and len(sys.argv) == 3:
            remove_relay(sys.argv[2])
        elif action == "get" and len(sys.argv) == 3:
            result = get_relay(sys.argv[2])
            print(json.dumps(result))
        elif action == "ensure-infrastructure" and len(sys.argv) == 2:
            ensure_infrastructure()
        else:
            print(
                "usage: smtp_relay.py set <domain> <host> <port> <user> <password>"
                "|remove <domain>|get <domain>|ensure-infrastructure",
                file=sys.stderr,
            )
            sys.exit(2)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
