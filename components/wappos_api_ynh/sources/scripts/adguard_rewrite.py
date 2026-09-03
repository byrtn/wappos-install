#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import ipaddress
import re
import subprocess
import sys
from pathlib import Path

import yaml

_CONFIG_PATH = Path("/var/www/adguardhome/AdGuardHome.yaml")
_DOMAIN_RE = re.compile(r"^\*?\.?[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?)*$")


def _validate_domain(domain: str) -> str:
    if not _DOMAIN_RE.match(domain):
        raise ValueError(f"Domaine invalide : {domain!r}")
    return domain


def _validate_ip(answer: str) -> str:
    ipaddress.ip_address(answer)
    return answer


def is_installed() -> bool:
    return _CONFIG_PATH.exists()


def _load() -> dict:
    with _CONFIG_PATH.open() as f:
        return yaml.safe_load(f)


def _save(data: dict) -> None:
    tmp_path = _CONFIG_PATH.with_suffix(".yaml.wappos_tmp")
    with tmp_path.open("w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
    tmp_path.replace(_CONFIG_PATH)


def _restart() -> None:
    subprocess.run(["systemctl", "restart", "adguardhome"], check=True, timeout=30)


def add_rewrite(domain: str, answer: str) -> None:
    domain = _validate_domain(domain)
    answer = _validate_ip(answer)
    data = _load()
    rewrites = data.setdefault("filtering", {}).setdefault("rewrites", [])
    rewrites[:] = [r for r in rewrites if r.get("domain") != domain]
    rewrites.append({"domain": domain, "answer": answer, "enabled": True})
    _save(data)
    _restart()


def remove_rewrite(domain: str) -> None:
    domain = _validate_domain(domain)
    data = _load()
    rewrites = data.get("filtering", {}).get("rewrites", [])
    before = len(rewrites)
    rewrites[:] = [r for r in rewrites if r.get("domain") != domain]
    if len(rewrites) != before:
        _save(data)
        _restart()


def list_rewrites() -> list[dict]:
    data = _load()
    return data.get("filtering", {}).get("rewrites", [])


def lan_ip() -> str:
    data = _load()
    bind_hosts = data.get("dns", {}).get("bind_hosts") or []
    if not bind_hosts:
        raise RuntimeError("Aucune adresse LAN trouvee dans dns.bind_hosts")
    return bind_hosts[0]


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "check":
        print("1" if is_installed() else "0")
    elif action == "add" and len(sys.argv) == 4:
        add_rewrite(sys.argv[2], sys.argv[3])
    elif action == "remove" and len(sys.argv) == 3:
        remove_rewrite(sys.argv[2])
    elif action == "list":
        for r in list_rewrites():
            print(f"{r.get('domain')}\t{r.get('answer')}\t{r.get('enabled')}")
    elif action == "lan-ip":
        print(lan_ip())
    else:
        print("usage: adguard_rewrite.py check|list|add <domain> <ip>|remove <domain>|lan-ip", file=sys.stderr)
        sys.exit(2)
