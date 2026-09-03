# Auteur : Patrick Ritaine

from __future__ import annotations

import subprocess

from wappos_api.errors import UpstreamProtocolError, UpstreamValidationError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/adguard_rewrite.py"
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
        raise UpstreamProtocolError("adguard_rewrite.py unreachable") from exc


def is_installed() -> bool:
    result = _run("check")
    return result.returncode == 0 and result.stdout.strip() == "1"


def list_rewrites() -> list[dict]:
    result = _run("list")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"adguard_rewrite.py list failed: {result.stderr.strip()}")
    rewrites = []
    for line in result.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        rewrites.append({"domain": parts[0], "answer": parts[1], "enabled": parts[2] == "True"})
    return rewrites


def add_rewrite(domain: str, answer: str) -> None:
    result = _run("add", domain, answer)
    if result.returncode != 0:
        raise UpstreamValidationError(
            f"adguard_rewrite.py add failed: {result.stderr.strip()}", error_key="adguard_rewrite_invalid"
        )


def remove_rewrite(domain: str) -> None:
    result = _run("remove", domain)
    if result.returncode != 0:
        raise UpstreamValidationError(
            f"adguard_rewrite.py remove failed: {result.stderr.strip()}", error_key="adguard_rewrite_invalid"
        )


def lan_ip() -> str:
    result = _run("lan-ip")
    if result.returncode != 0:
        raise UpstreamProtocolError(f"adguard_rewrite.py lan-ip failed: {result.stderr.strip()}")
    return result.stdout.strip()
