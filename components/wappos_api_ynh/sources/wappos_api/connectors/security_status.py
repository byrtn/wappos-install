# Auteur : Patrick Ritaine

from __future__ import annotations

import json
import subprocess

from wappos_api.errors import UpstreamProtocolError

_SCRIPT_PATH = "/opt/yunohost/wappos_api/scripts/security_status.py"
_TIMEOUT_SECONDS = 20


def overview() -> dict:
    try:
        result = subprocess.run(
            ["sudo", "-n", "python3", _SCRIPT_PATH, "overview"],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT_SECONDS,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise UpstreamProtocolError("security_status.py unreachable") from exc
    if result.returncode != 0:
        raise UpstreamProtocolError(f"security_status.py overview failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise UpstreamProtocolError("security_status.py overview returned invalid JSON") from exc
