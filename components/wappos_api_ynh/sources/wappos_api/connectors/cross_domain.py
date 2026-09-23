# Auteur : Patrick Ritaine

from __future__ import annotations

import subprocess

from wappos_api.errors import UpstreamProtocolError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/cross_domain.py"
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
        raise UpstreamProtocolError("cross_domain.py unreachable") from exc


def status(app_id: str) -> bool:
    result = _run("status", app_id)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py status failed: {result.stderr.strip()}")
    return result.stdout.strip() == "1"


def enable(app_id: str) -> None:
    result = _run("enable", app_id)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py enable failed: {result.stderr.strip()}")


def disable(app_id: str) -> None:
    result = _run("disable", app_id)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py disable failed: {result.stderr.strip()}")


def list_domains(app_id: str) -> list[str]:
    result = _run("list-domains", app_id)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py list-domains failed: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line]


def add_domain(app_id: str, domain: str) -> None:
    result = _run("add-domain", app_id, domain)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py add-domain failed: {result.stderr.strip()}")


def remove_domain(app_id: str, domain: str) -> None:
    result = _run("remove-domain", app_id, domain)
    if result.returncode != 0:
        raise UpstreamProtocolError(f"cross_domain.py remove-domain failed: {result.stderr.strip()}")
