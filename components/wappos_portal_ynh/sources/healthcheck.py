# Auteur : Patrick Ritaine
import json
import smtplib
import subprocess
import sys
from email.message import EmailMessage
from pathlib import Path

STATE_FILE = Path(__file__).parent / "data" / "healthcheck_state.json"
APP = sys.argv[1] if len(sys.argv) > 1 else "wappos_portal"
PORT = sys.argv[2] if len(sys.argv) > 2 else "9300"
ALERT_TO = sys.argv[3] if len(sys.argv) > 3 else "root"


def _yunohost_version() -> str:
    try:
        return subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", "yunohost"],
            capture_output=True, text=True, timeout=10, check=True,
        ).stdout.strip()
    except Exception as e:
        return f"unknown ({e})"


def _service_active(name: str) -> bool:
    return subprocess.run(
        ["systemctl", "is-active", "--quiet", name], timeout=10
    ).returncode == 0


def _app_reachable() -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/", timeout=10) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            return resp.status == 200 and "wappos portal" in body.lower()
    except Exception:
        return False


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))


def _send_alert(subject: str, body: str) -> None:
    msg = EmailMessage()
    msg["From"] = "wappos-portal-healthcheck@localhost"
    msg["To"] = ALERT_TO
    msg["Subject"] = subject
    msg.set_content(body, charset="utf-8")

    smtp = smtplib.SMTP("localhost")
    smtp.send_message(msg)
    smtp.quit()


def main() -> None:
    yunohost_version = _yunohost_version()
    service_ok = _service_active(APP)
    portalapi_ok = _service_active("yunohost-portal-api")
    reachable = _app_reachable()
    status_ok = service_ok and portalapi_ok and reachable

    state = _load_state()
    version_changed = state.get("yunohost_version") not in (None, yunohost_version)
    status_changed = state.get("status_ok") is not None and state.get("status_ok") != status_ok

    if version_changed or status_changed or (not status_ok and "status_ok" not in state):
        if not status_ok:
            headline = (
                "A functional problem was detected on wappos-portal.\n"
                "Nothing was fixed automatically — check the app manually "
                "(login, tiles, profile editing) as soon as possible."
            )
        elif version_changed:
            headline = (
                "YunoHost was updated since the last check.\n"
                "wappos-portal relies on undocumented internal YunoHost details "
                "(see cahier des charges section 9bis): manually verify that "
                "login, tiles, and profile editing still work."
            )
        else:
            headline = "wappos-portal's status changed since the last check."

        details = (
            f"{headline}\n\n"
            "--- Details ---\n"
            f"Previously known YunoHost version : {state.get('yunohost_version', 'unknown')}\n"
            f"Current YunoHost version           : {yunohost_version}\n\n"
            f"wappos_portal service active      : {'yes' if service_ok else 'NO'}\n"
            f"yunohost-portal-api service active : {'yes' if portalapi_ok else 'NO'}\n"
            f"Home page reachable and correct    : {'yes' if reachable else 'NO'}"
        )
        if not status_ok:
            subject = "[wappos-portal] ALERT: functional problem detected"
        else:
            subject = "[wappos-portal] YunoHost update detected — please verify"
        try:
            _send_alert(subject, details)
        except Exception as e:
            print(f"[wappos-portal healthcheck] failed to send alert: {e}", file=sys.stderr)

    _save_state({"yunohost_version": yunohost_version, "status_ok": status_ok})


if __name__ == "__main__":
    main()
