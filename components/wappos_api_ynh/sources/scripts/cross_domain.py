#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import json
import re
import subprocess
import sys
from pathlib import Path

_REGISTRY_PATH = Path("/etc/yunohost/wappos_cross_domain_apps.json")
_APP_ID_RE = re.compile(r"^[a-z0-9_]+$")


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=60)


def _load_registry() -> dict:
    if not _REGISTRY_PATH.exists():
        return {}
    return json.loads(_REGISTRY_PATH.read_text())


def _save_registry(data: dict) -> None:
    _REGISTRY_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))


def _all_domains() -> list[str]:
    result = _run("yunohost", "domain", "list", "--output-as", "json")
    return json.loads(result.stdout)["domains"]


def _installed_apps() -> set[str]:
    result = _run("yunohost", "app", "list", "--output-as", "json")
    return {a["id"] for a in json.loads(result.stdout)["apps"]}


def _validate_app_id(app_id: str) -> str:
    if not _APP_ID_RE.match(app_id):
        raise ValueError(f"Identifiant d'app invalide : {app_id!r}")
    if app_id not in _installed_apps():
        raise ValueError(f"App non installee : {app_id!r}")
    return app_id


def _app_domain_path(app_id: str) -> tuple[str, str]:
    domain = _run("yunohost", "app", "setting", app_id, "domain").stdout.strip()
    path = _run("yunohost", "app", "setting", app_id, "path").stdout.strip()
    if not domain or not path:
        raise ValueError(f"App {app_id!r} n'a pas de domaine/chemin (pas une app web standard)")
    return domain, path


def _nginx_conf_path(domain: str, app_id: str) -> Path:
    return Path(f"/etc/nginx/conf.d/{domain}.d/{app_id}.conf")


def _add_url(app_id: str, url: str) -> bool:
    result = subprocess.run(
        [
            "python3",
            "-c",
            "from yunohost.permission import permission_url; "
            f"permission_url({app_id!r} + '.main', add_url=[{url!r}], sync_perm=False)",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return "YunohostValidationError" not in result.stderr and "YunohostError" not in result.stderr


def _remove_url(app_id: str, url: str) -> None:
    subprocess.run(
        [
            "python3",
            "-c",
            "from yunohost.permission import permission_url; "
            f"permission_url({app_id!r} + '.main', remove_url=[{url!r}], sync_perm=False)",
        ],
        check=False,
    )


def _sync() -> None:
    _run("yunohost", "app", "ssowatconf")


def enable(app_id: str) -> None:
    _validate_app_id(app_id)
    home_domain, path = _app_domain_path(app_id)
    home_conf = _nginx_conf_path(home_domain, app_id)
    if not home_conf.exists():
        raise ValueError(f"Pas de fragment nginx trouve pour {app_id!r} sur {home_domain!r}")
    conf_content = home_conf.read_text()

    for domain in _all_domains():
        if domain == home_domain:
            continue
        if not _add_url(app_id, f"{domain}{path}"):
            continue
        target = _nginx_conf_path(domain, app_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(conf_content)

    _run("nginx", "-t")
    _run("systemctl", "reload", "nginx")
    _sync()

    registry = _load_registry()
    registry[app_id] = {"home_domain": home_domain, "path": path}
    _save_registry(registry)


def disable(app_id: str) -> None:
    _validate_app_id(app_id)
    registry = _load_registry()
    entry = registry.pop(app_id, None)
    if entry is None:
        return
    home_domain = entry["home_domain"]
    path = entry["path"]

    for domain in _all_domains():
        if domain == home_domain:
            continue
        target = _nginx_conf_path(domain, app_id)
        if target.exists():
            target.unlink()
        _remove_url(app_id, f"{domain}{path}")

    _run("nginx", "-t")
    _run("systemctl", "reload", "nginx")
    _sync()
    _save_registry(registry)


def status(app_id: str) -> bool:
    _validate_app_id(app_id)
    return app_id in _load_registry()


def apply_to_new_domain(domain: str) -> None:
    if domain not in _all_domains():
        raise ValueError(f"Domaine inconnu : {domain!r}")
    registry = _load_registry()
    changed = False
    for app_id, entry in registry.items():
        home_domain = entry["home_domain"]
        path = entry["path"]
        if domain == home_domain:
            continue
        home_conf = _nginx_conf_path(home_domain, app_id)
        if not home_conf.exists():
            continue
        if not _add_url(app_id, f"{domain}{path}"):
            continue
        target = _nginx_conf_path(domain, app_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(home_conf.read_text())
        changed = True

    if changed:
        _run("nginx", "-t")
        _run("systemctl", "reload", "nginx")
        _sync()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if action == "enable" and len(sys.argv) == 3:
            enable(sys.argv[2])
        elif action == "disable" and len(sys.argv) == 3:
            disable(sys.argv[2])
        elif action == "status" and len(sys.argv) == 3:
            print("1" if status(sys.argv[2]) else "0")
        elif action == "apply-to-new-domain" and len(sys.argv) == 3:
            apply_to_new_domain(sys.argv[2])
        else:
            print(
                "usage: cross_domain.py enable|disable|status <app_id>|apply-to-new-domain <domain>",
                file=sys.stderr,
            )
            sys.exit(2)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
