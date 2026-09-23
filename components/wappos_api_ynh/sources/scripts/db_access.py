#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import json
import sys
from pathlib import Path

import yaml

_APPS_DIR = Path("/etc/yunohost/apps")


def _read_db_credentials(app_id: str) -> dict | None:
    settings_path = _APPS_DIR / app_id / "settings.yml"
    if not settings_path.exists():
        return None
    data = yaml.safe_load(settings_path.read_text()) or {}
    db_name = data.get("db_name")
    db_user = data.get("db_user")
    db_pwd = data.get("db_pwd")
    if not db_name or not db_user or not db_pwd:
        return None
    return {"db_name": db_name, "db_user": db_user, "db_pwd": db_pwd}


def list_all() -> dict:
    result = {}
    if not _APPS_DIR.is_dir():
        return result
    for app_dir in _APPS_DIR.iterdir():
        credentials = _read_db_credentials(app_dir.name)
        if credentials is not None:
            result[app_dir.name] = {"db_name": credentials["db_name"], "db_user": credentials["db_user"]}
    return result


def get(app_id: str) -> dict | None:
    return _read_db_credentials(app_id)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "list-all" and len(sys.argv) == 2:
        print(json.dumps(list_all()))
    elif action == "get" and len(sys.argv) == 3:
        print(json.dumps(get(sys.argv[2])))
    else:
        print("usage: db_access.py list-all|get <app_id>", file=sys.stderr)
        sys.exit(2)
