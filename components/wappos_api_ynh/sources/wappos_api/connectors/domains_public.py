# Auteur : Patrick Ritaine

from __future__ import annotations

import json
import subprocess

from wappos_api.errors import UpstreamProtocolError

_TIMEOUT_SECONDS = 15


def list_domain_names() -> list[str]:
    try:
        result = subprocess.run(
            ["sudo", "-n", "/usr/bin/yunohost", "domain", "list", "--output-as", "json"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise UpstreamProtocolError("yunohost domain list unreachable") from exc
    if result.returncode != 0:
        raise UpstreamProtocolError(f"yunohost domain list failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout).get("domains", [])
    except ValueError as exc:
        raise UpstreamProtocolError("yunohost domain list returned invalid JSON") from exc
