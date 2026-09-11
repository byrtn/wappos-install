# Auteur : Patrick Ritaine

from __future__ import annotations

import subprocess

from wappos_api.errors import UpstreamProtocolError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/ssh_access.py"
_TIMEOUT_SECONDS = 15


def _run(*args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["sudo", "-n", "python3", _SCRIPT_PATH, *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise UpstreamProtocolError("ssh_access.py unreachable") from exc


def password_auth_enabled() -> bool:
    result = _run("status")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"ssh_access.py status failed: {result.stderr.strip()}")
    return result.stdout.strip() == "1"


def enable_password_auth() -> None:
    result = _run("enable")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"ssh_access.py enable failed: {result.stderr.strip()}")


def disable_password_auth() -> None:
    result = _run("disable")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"ssh_access.py disable failed: {result.stderr.strip()}")
