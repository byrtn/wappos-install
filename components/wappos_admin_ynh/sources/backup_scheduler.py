# Auteur : Patrick Ritaine
import json
import smtplib
import subprocess
import sys
from datetime import date, datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

_ARGS = [a for a in sys.argv[1:] if a != "--force"]
FORCE_RUN = "--force" in sys.argv[1:]
ALERT_TO = _ARGS[0] if _ARGS else "root"

_INSTALL_DIR = Path(__file__).parent
_SCHEDULE_FILE = _INSTALL_DIR / "data" / "backup_schedule.json"
_HISTORY_FILE = _INSTALL_DIR / "data" / "backup_history.json"
_WAPPOS_API_BACKUPS_CACHE_FILE = Path("/dev/shm/wappos_api_cache/list_backups.cache")


def _invalidate_wappos_api_backups_cache() -> None:
    _WAPPOS_API_BACKUPS_CACHE_FILE.unlink(missing_ok=True)

_DEFAULT_SCHEDULE = {
    "enabled": True,
    "frequency": "daily",
    "scope": "full",
    "apps": [],
    "last_run": None,
    "retention_enabled": True,
    "retention_mode": "count",
    "retention_keep_count": 2,
    "retention_keep_days": 2,
}


def _load_schedule() -> dict:
    if not _SCHEDULE_FILE.exists():
        return dict(_DEFAULT_SCHEDULE)
    try:
        data = json.loads(_SCHEDULE_FILE.read_text())
    except (ValueError, OSError):
        return dict(_DEFAULT_SCHEDULE)
    merged = dict(_DEFAULT_SCHEDULE)
    merged.update(data)
    return merged


def _save_schedule(schedule: dict) -> None:
    _SCHEDULE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SCHEDULE_FILE.write_text(json.dumps(schedule, indent=2, sort_keys=True))


def _load_history() -> list[dict]:
    if not _HISTORY_FILE.exists():
        return []
    try:
        return json.loads(_HISTORY_FILE.read_text())
    except (ValueError, OSError):
        return []


def _save_history(history: list[dict]) -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    _HISTORY_FILE.write_text(json.dumps(history[-200:], indent=2, sort_keys=True))


def _is_due(schedule: dict) -> bool:
    if not schedule.get("enabled"):
        return False
    last_run = schedule.get("last_run")
    if not last_run:
        return True
    try:
        last_date = date.fromisoformat(last_run)
    except ValueError:
        return True
    today = date.today()
    if schedule.get("frequency") == "weekly":
        return (today - last_date).days >= 7
    return today > last_date


def _extract_trailing_json(text: str) -> dict | None:
    idx = text.rfind("{")
    while idx != -1:
        try:
            return json.loads(text[idx:])
        except ValueError:
            idx = text.rfind("{", 0, idx)
    return None


def _find_archive_created_after(started_at: datetime) -> str | None:
    try:
        result = subprocess.run(
            ["yunohost", "backup", "list", "--output-as", "json"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return None
    data = _extract_trailing_json(result.stdout)
    if data is None:
        return None
    cutoff = started_at - timedelta(minutes=1)
    for name in reversed(data.get("archives", [])):
        try:
            stamp = datetime.strptime(name[:15], "%Y%m%d-%H%M%S")
        except ValueError:
            continue
        if stamp >= cutoff:
            return name
    return None


def _run_backup(schedule: dict) -> dict | None:
    cmd = ["yunohost", "backup", "create", "--output-as", "json"]
    if schedule.get("scope") == "apps" and schedule.get("apps"):
        cmd += ["--apps", *schedule["apps"]]

    started_at = datetime.now()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    except (subprocess.SubprocessError, OSError) as e:
        return {"timestamp": datetime.now().isoformat(), "status": "ERROR", "detail": str(e)}

    data = _extract_trailing_json(result.stdout)
    if data is None:
        archive_name = _find_archive_created_after(started_at)
        if archive_name:
            return {
                "timestamp": datetime.now().isoformat(), "name": archive_name,
                "status": "COMPLETE", "failed_targets": [],
                "detail": (
                    "Sauvegarde réussie, confirmée via 'yunohost backup list' — la sortie de "
                    "'yunohost backup create' n'a pas pu être décodée en JSON (souvent un avertissement "
                    "texte d'une app, ex. SOGo recommandant d'arrêter son service avant sauvegarde)."
                ),
            }
        return {
            "timestamp": datetime.now().isoformat(), "status": "ERROR",
            "detail": (
                f"sortie JSON illisible (code {result.returncode}) — "
                f"stdout: {result.stdout[-800:]!r} — stderr: {result.stderr[:800]!r}"
            ),
        }

    targets = data.get("results", {})
    failed = [
        name for category in ("apps", "system")
        for name, status in targets.get(category, {}).items()
        if status not in ("Success", "Warning")
    ]

    return {
        "timestamp": datetime.now().isoformat(),
        "name": data.get("name"),
        "status": "INCOMPLETE" if failed else "COMPLETE",
        "failed_targets": failed,
        "size": data.get("size"),
    }


def _run_retention_cleanup(schedule: dict) -> list[dict]:
    if not schedule.get("retention_enabled"):
        return []

    try:
        result = subprocess.run(
            ["yunohost", "backup", "list", "--output-as", "json"],
            capture_output=True, text=True, timeout=60,
        )
    except (subprocess.SubprocessError, OSError):
        return [{"name": "?", "status": "ERROR", "detail": "impossible de lister les sauvegardes"}]

    data = _extract_trailing_json(result.stdout)
    if data is None:
        return [{"name": "?", "status": "ERROR", "detail": "impossible de lister les sauvegardes"}]
    archives = data.get("archives", [])

    to_delete = []
    if schedule.get("retention_mode") == "days":
        cutoff = datetime.now() - timedelta(days=schedule.get("retention_keep_days", 30))
        for name in archives:
            try:
                stamp = datetime.strptime(name[:15], "%Y%m%d-%H%M%S")
            except ValueError:
                continue
            if stamp < cutoff:
                to_delete.append(name)
    else:
        keep_count = schedule.get("retention_keep_count", 5)
        if len(archives) > keep_count:
            to_delete = archives[: len(archives) - keep_count]

    deleted = []
    for name in to_delete:
        try:
            subprocess.run(
                ["yunohost", "backup", "delete", name, "--output-as", "json"],
                capture_output=True, text=True, timeout=120, check=True,
            )
            deleted.append({"name": name, "status": "DELETED"})
        except subprocess.SubprocessError:
            deleted.append({"name": name, "status": "ERROR"})
    return deleted


def _send_report(backup_result: dict | None, deletions: list[dict]) -> None:
    msg = EmailMessage()
    msg["From"] = "wappos-admin-backup-scheduler@localhost"
    msg["To"] = ALERT_TO
    msg["Subject"] = "[wappos-admin] Sauvegarde automatique — anomalie détectée"

    lines = []
    if backup_result:
        lines.append(f"- Sauvegarde {backup_result.get('name', '?')} : {backup_result['status']}")
        if backup_result.get("failed_targets"):
            lines.append(f"  Cibles en échec : {', '.join(backup_result['failed_targets'])}")
        if backup_result.get("detail"):
            lines.append(f"  Détail : {backup_result['detail']}")
    for d in deletions:
        if d["status"] == "ERROR":
            lines.append(f"- Suppression de {d['name']} : ÉCHEC")

    body = (
        "Vérification quotidienne de la sauvegarde automatique — au moins un écart a été détecté :\n\n"
        + "\n".join(lines)
    )
    msg.set_content(body, charset="utf-8")

    smtp = smtplib.SMTP("localhost")
    smtp.send_message(msg)
    smtp.quit()


def main() -> None:
    schedule = _load_schedule()
    backup_result = None

    if FORCE_RUN or _is_due(schedule):
        backup_result = _run_backup(schedule)
        history = _load_history()
        history.append(backup_result)
        _save_history(history)
        schedule["last_run"] = date.today().isoformat()
        _save_schedule(schedule)

    deletions = _run_retention_cleanup(schedule)

    if backup_result is not None or deletions:
        _invalidate_wappos_api_backups_cache()

    anomaly = (backup_result and backup_result["status"] != "COMPLETE") or any(
        d["status"] == "ERROR" for d in deletions
    )
    if anomaly:
        _send_report(backup_result, deletions)


if __name__ == "__main__":
    main()
