# Auteur : Patrick Ritaine

from __future__ import annotations

import json
import subprocess

from wappos_api.errors import UpstreamProtocolError, UpstreamValidationError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/smtp_relay.py"
_TIMEOUT_SECONDS = 60


def _run(*args: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["sudo", "-n", "python3", _SCRIPT_PATH, *args],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise UpstreamProtocolError("smtp_relay.py unreachable") from exc


def get_relay(domain: str) -> dict | None:
    result = _run("get", domain)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"smtp_relay.py get failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout) if result.stdout.strip() else None
    except ValueError as exc:
        raise UpstreamProtocolError("smtp_relay.py get returned an unexpected payload") from exc


def set_relay(domain: str, host: str, port: int, user: str, password: str) -> None:
    result = _run("set", domain, host, str(port), user, password)
    if result.returncode != 0:
        message = result.stderr.strip() or "smtp_relay.py set failed"
        raise UpstreamValidationError(message, error_key="invalid_smtp_relay", detail=domain)


def remove_relay(domain: str) -> None:
    result = _run("remove", domain)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"smtp_relay.py remove failed: {result.stderr.strip()}")
