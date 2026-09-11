#!/usr/bin/env python3
# Auteur : Patrick Ritaine

import re
import subprocess
import sys
from pathlib import Path

_SSHD_CONFIG_PATH = Path("/etc/ssh/sshd_config")
_PASSWORD_AUTH_RE = re.compile(r"^\s*PasswordAuthentication\s+(yes|no)\s*$", re.IGNORECASE | re.MULTILINE)


def password_auth_enabled() -> bool:
    content = _SSHD_CONFIG_PATH.read_text()
    match = _PASSWORD_AUTH_RE.search(content)
    if not match:
        return False
    return match.group(1).lower() == "yes"


def _set_password_auth(enabled: bool) -> None:
    value = "yes" if enabled else "no"
    content = _SSHD_CONFIG_PATH.read_text()
    if _PASSWORD_AUTH_RE.search(content):
        content = _PASSWORD_AUTH_RE.sub(f"PasswordAuthentication {value}", content)
    else:
        content = content.rstrip("\n") + f"\nPasswordAuthentication {value}\n"
    tmp_path = _SSHD_CONFIG_PATH.with_suffix(".wappos_tmp")
    tmp_path.write_text(content)
    tmp_path.chmod(0o644)
    subprocess.run(["sshd", "-t", "-f", str(tmp_path)], check=True, timeout=10)
    tmp_path.replace(_SSHD_CONFIG_PATH)
    subprocess.run(["systemctl", "reload", "ssh"], check=True, timeout=15)


def enable_password_auth() -> None:
    _set_password_auth(True)


def disable_password_auth() -> None:
    _set_password_auth(False)


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "status":
        print("1" if password_auth_enabled() else "0")
    elif action == "enable":
        enable_password_auth()
    elif action == "disable":
        disable_password_auth()
    else:
        print("usage: ssh_access.py status|enable|disable", file=sys.stderr)
        sys.exit(2)
