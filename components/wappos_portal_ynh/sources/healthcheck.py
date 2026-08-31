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
                "Un problème de fonctionnement a été détecté sur wappos-portal.\n"
                "Rien n'a été corrigé automatiquement — vérifie manuellement l'app "
                "(connexion, tuiles, édition de profil) dès que possible."
            )
        elif version_changed:
            headline = (
                "YunoHost a été mis à jour depuis la dernière vérification.\n"
                "Wappos-portal dépend de détails internes non documentés de YunoHost "
                "(cf. cahier des charges section 9bis) : vérifie manuellement que la "
                "connexion, les tuiles et l'édition de profil fonctionnent toujours."
            )
        else:
            headline = "L'état de wappos-portal a changé depuis la dernière vérification."

        details = (
            f"{headline}\n\n"
            "--- Détails ---\n"
            f"Version YunoHost précédemment connue : {state.get('yunohost_version', 'inconnue')}\n"
            f"Version YunoHost actuelle            : {yunohost_version}\n\n"
            f"Service wappos_portal actif      : {'oui' if service_ok else 'NON'}\n"
            f"Service yunohost-portal-api actif : {'oui' if portalapi_ok else 'NON'}\n"
            f"Page d'accueil accessible et correcte : {'oui' if reachable else 'NON'}"
        )
        if not status_ok:
            subject = "[wappos-portal] ALERTE : problème de fonctionnement détecté"
        else:
            subject = "[wappos-portal] Mise à jour YunoHost détectée — à vérifier"
        try:
            _send_alert(subject, details)
        except Exception as e:
            print(f"[wappos-portal healthcheck] échec d'envoi de l'alerte : {e}", file=sys.stderr)

    _save_state({"yunohost_version": yunohost_version, "status_ok": status_ok})


if __name__ == "__main__":
    main()
