#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

_ROOT_AUTHORIZED_KEYS = Path("/root/.ssh/authorized_keys")
_SHADOW_PATH = Path("/etc/shadow")


def root_password_last_changed() -> dict:
    for line in _SHADOW_PATH.read_text().splitlines():
        fields = line.split(":")
        if fields[0] == "root" and len(fields) > 2 and fields[2]:
            days_since_epoch = int(fields[2])
            changed_at = days_since_epoch * 86400
            return {"last_changed_epoch": changed_at}
    return {"last_changed_epoch": None}


def fail2ban_summary() -> dict:
    try:
        result = subprocess.run(
            ["fail2ban-client", "banned"], capture_output=True, text=True, timeout=15
        )
    except (subprocess.TimeoutExpired, OSError):
        return {"available": False, "jails": {}, "total_banned": 0}
    if result.returncode != 0:
        return {"available": False, "jails": {}, "total_banned": 0}
    try:
        parsed = ast.literal_eval(result.stdout.strip())
    except (ValueError, SyntaxError):
        return {"available": False, "jails": {}, "total_banned": 0}
    jails: dict[str, list[str]] = {}
    total = 0
    for entry in parsed:
        for jail, ips in entry.items():
            jails[jail] = ips
            total += len(ips)
    return {"available": True, "jails": jails, "total_banned": total}


def root_ssh_keys() -> list[dict]:
    if not _ROOT_AUTHORIZED_KEYS.exists():
        return []
    try:
        result = subprocess.run(
            ["ssh-keygen", "-lf", str(_ROOT_AUTHORIZED_KEYS)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []
    if result.returncode != 0:
        return []
    keys = []
    for line in result.stdout.strip().splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue
        keys.append(
            {
                "bits": parts[0],
                "fingerprint": parts[1],
                "comment": " ".join(parts[2:-1]),
                "type": parts[-1].strip("()"),
            }
        )
    return keys


def overview() -> dict:
    return {
        "root_password": root_password_last_changed(),
        "fail2ban": fail2ban_summary(),
        "root_ssh_keys": root_ssh_keys(),
        "generated_at": int(time.time()),
    }


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "overview":
        print(json.dumps(overview()))
    else:
        print("usage: security_status.py overview", file=sys.stderr)
        sys.exit(2)
