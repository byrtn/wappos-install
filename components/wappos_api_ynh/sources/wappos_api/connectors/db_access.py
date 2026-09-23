# Auteur : Patrick Ritaine

from __future__ import annotations

import json
import subprocess

from wappos_api.errors import UpstreamProtocolError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/db_access.py"
_TIMEOUT_SECONDS = 30


def _run(*args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["sudo", "-n", "python3", _SCRIPT_PATH, *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise UpstreamProtocolError("db_access.py unreachable") from exc


def list_all() -> dict[str, dict[str, str]]:
    result = _run("list-all")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"db_access.py list-all failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout) if result.stdout.strip() else {}
    except ValueError as exc:
        raise UpstreamProtocolError("db_access.py list-all returned an unexpected payload") from exc


def get_credentials(app_id: str) -> dict[str, str] | None:
    result = _run("get", app_id)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"db_access.py get failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError as exc:
        raise UpstreamProtocolError("db_access.py get returned an unexpected payload") from exc
