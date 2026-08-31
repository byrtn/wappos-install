# Auteur : Patrick Ritaine

from __future__ import annotations

import base64
import json
import math
import os
import re
import secrets
import subprocess
import threading
import time
import tomllib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote, urlencode
from zoneinfo import ZoneInfo

import requests
from flask import Flask, Response, abort, jsonify, redirect, render_template, request, session, stream_with_context, url_for
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest, multiprocess
from werkzeug.middleware.proxy_fix import ProxyFix

import backup_scheduler
import docker_gate
import docker_progress

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)


@app.context_processor
def _inject_year():
    return {"year": datetime.now().year}


@app.after_request
def _no_store_dynamic_pages(response):
    if not request.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
    return response

_secret_key_file = Path(__file__).parent / ".package" / "secret_key"
if not _secret_key_file.exists():
    _secret_key_file.parent.mkdir(parents=True, exist_ok=True)
    _secret_key_file.write_text(secrets.token_hex(32))
app.secret_key = _secret_key_file.read_text().strip()

app.config["SESSION_COOKIE_NAME"] = "wappos_admin_session"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=3)

_metrics_token_file = Path(__file__).parent / ".package" / "metrics_token"
if not _metrics_token_file.exists():
    _metrics_token_file.parent.mkdir(parents=True, exist_ok=True)
    _metrics_token_file.write_text(secrets.token_hex(32))
METRICS_TOKEN = _metrics_token_file.read_text().strip()

_REQUEST_COUNT = Counter(
    "wappos_admin_requests_total", "Nombre de requêtes HTTP traitées",
    ["method", "endpoint", "status"],
)
_REQUEST_LATENCY = Histogram(
    "wappos_admin_request_duration_seconds", "Durée des requêtes HTTP",
    ["method", "endpoint"],
)
_PROCESS_MEMORY = Gauge(
    "wappos_admin_process_resident_memory_bytes", "Mémoire résidente du worker",
    multiprocess_mode="livesum",
)


def _current_rss_bytes() -> int:
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1]) * 1024
    except OSError:
        pass
    return 0


@app.before_request
def _metrics_start_timer():
    request._metrics_start = time.monotonic()


@app.after_request
def _metrics_record(response):
    _PROCESS_MEMORY.set(_current_rss_bytes())
    start = getattr(request, "_metrics_start", None)
    if start is not None:
        endpoint = request.endpoint or "unknown"
        _REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(time.monotonic() - start)
        _REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()
    return response


def _generate_metrics() -> bytes:
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        return generate_latest(registry)
    return generate_latest()


@app.route("/metrics")
def metrics():
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    if not secrets.compare_digest(token, METRICS_TOKEN):
        abort(403)
    return Response(_generate_metrics(), mimetype=CONTENT_TYPE_LATEST)


@app.template_filter("relative_fr")
def _relative_fr(epoch: float | None) -> str:
    if not epoch:
        return "jamais"
    delta = datetime.now().timestamp() - epoch
    if delta < 60:
        return "il y a quelques secondes"
    if delta < 3600:
        minutes = int(delta // 60)
        return f"il y a {minutes} minute{'s' if minutes > 1 else ''}"
    if delta < 86400:
        hours = int(delta // 3600)
        return f"il y a {hours} heure{'s' if hours > 1 else ''}"
    days = int(delta // 86400)
    return f"il y a {days} jour{'s' if days > 1 else ''}"


@app.template_filter("service_since")
def _service_since(value) -> str:
    if value is None or value == "unknown":
        return "inconnu"
    if isinstance(value, (int, float)):
        return _relative_fr(value)
    return str(value)


_SERVICE_SUBSTATE_FR = {
    "running": "En cours d'exécution",
    "exited": "Terminé (oneshot)",
    "dead": "Arrêté",
    "failed": "En échec",
    "activating": "Démarrage en cours",
    "deactivating": "Arrêt en cours",
    "reload": "Rechargement en cours",
    "unknown": "Inconnu",
}


@app.template_filter("service_status_fr")
def _service_status_fr(status: str) -> str:
    return _SERVICE_SUBSTATE_FR.get(status, (status or "").capitalize())


_UNIT_RESULT_FR = {
    "success": "Succès",
    "resources": "Ressources indisponibles",
    "timeout": "Délai dépassé",
    "exit-code": "Code de sortie non nul",
    "signal": "Arrêté par un signal",
    "core-dump": "Crash (core dump)",
    "watchdog": "Timeout du watchdog",
    "start-limit-hit": "Trop de redémarrages",
    "oom-kill": "Tué par manque de mémoire (OOM)",
    "protocol": "Erreur de protocole",
}


@app.template_filter("unit_result_fr")
def _unit_result_fr(result: str) -> str:
    return _UNIT_RESULT_FR.get(result, (result or "inconnu").capitalize())


_LOCAL_TZ = ZoneInfo("Europe/Paris")


def _parse_yunohost_datetime(value) -> datetime | None:
    if not value:
        return None
    text = str(value)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:19], fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


@app.template_filter("backup_date_fr")
def _backup_date_fr(value) -> str:
    if not value:
        return "—"
    parsed = _parse_yunohost_datetime(value)
    if parsed is None:
        return str(value)
    return parsed.astimezone(_LOCAL_TZ).strftime("%d/%m/%Y %H:%M")


_MOIS_FR = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]


def _day_label_fr(day_key: str) -> str:
    try:
        d = datetime.strptime(day_key, "%Y-%m-%d")
    except ValueError:
        return day_key
    return f"{d.day} {_MOIS_FR[d.month - 1]} {d.year}"


@app.template_filter("colorize_log_line")
def _colorize_log_line(line: str):
    from markupsafe import Markup, escape

    for keyword, css_class in (
        ("ERROR", "log-line-error"), ("WARNING", "log-line-warning"),
        ("SUCCESS", "log-line-success"), ("INFO", "log-line-info"),
    ):
        if f"{keyword} -" in line:
            return Markup(f'<span class="{css_class}">{escape(line)}</span>')
    return Markup(escape(line))

WAPPOS_API_BASE = "http://127.0.0.1:9400"

_MANIFEST = tomllib.loads((Path(__file__).parent / ".package" / "manifest.toml").read_text())
APP_VERSION = _MANIFEST["version"]

_HIDDEN_SYSTEM_USERS = {"cron.alerts"}


@app.before_request
def _require_login():
    if request.path.startswith("/static") or request.path in ("/login", "/metrics"):
        return None
    if _current_user():
        return None
    return render_template("login.html", app_version=APP_VERSION, year=datetime.now().year), 401


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    try:
        token = _wappos_api_admin_login(username, password)
    except requests.exceptions.HTTPError:
        return render_template(
            "login.html", app_version=APP_VERSION, year=datetime.now().year,
            error="Identifiant ou mot de passe incorrect.",
        ), 401
    except requests.exceptions.RequestException:
        return render_template(
            "login.html", app_version=APP_VERSION, year=datetime.now().year,
            error="Serveur injoignable, réessayez.",
        ), 503
    session.permanent = True
    session["user"] = username
    session["token"] = token
    return redirect(url_for("home"))


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


class SessionExpiredError(Exception):
    pass


def _raise_for_status(resp: "requests.Response") -> None:
    if resp.status_code == 401:
        raise SessionExpiredError()
    resp.raise_for_status()


@app.errorhandler(SessionExpiredError)
def _handle_session_expired(_exc):
    session.clear()
    return render_template(
        "login.html", app_version=APP_VERSION, year=datetime.now().year,
        error="Ta session a expiré, reconnecte-toi.",
    ), 401


@app.errorhandler(404)
def _handle_not_found(exc):
    user = _current_user()
    app.logger.warning(
        "404 %s %s (user=%r, cause=%r)", request.method, request.path, user, str(exc),
    )
    if not user:
        return render_template("login.html", app_version=APP_VERSION, year=datetime.now().year), 401
    return render_template("not_found.html", user=user, app_version=APP_VERSION), 404

_ERROR_MESSAGES = {
    "user_already_exists": "Cet identifiant existe déjà.",
    "user_unknown": "Utilisateur inconnu.",
    "user_cannot_delete_last_admin": "Impossible de supprimer le dernier administrateur.",
    "invalid_password": "Mot de passe invalide (trop faible ou incompatible).",
    "group_unknown": "Groupe inconnu.",
    "permission_protected": "Cette permission est protégée — les visiteurs ne peuvent pas y être ajoutés directement.",
    "permission_require_account": "Ce type de permission nécessite un compte (pas accessible aux visiteurs).",
    "permission_cant_add_to_all_users": "Impossible d'ajouter tous les utilisateurs à cette permission.",
    "diagnosis_unknown_categories": "Catégorie de diagnostic inconnue.",
    "group_already_exist": "Ce groupe existe déjà.",
    "group_cannot_be_deleted": "Ce groupe ne peut pas être supprimé.",
    "group_cannot_edit_all_users": "Le groupe 'Tous les comptes' ne peut pas être modifié directement.",
    "group_cannot_edit_visitors": "Le groupe 'Visiteurs' ne peut pas être modifié directement.",
    "group_cannot_edit_primary_group": "Ce groupe personnel ne peut pas être modifié directement.",
    "group_cannot_remove_last_admin": "Impossible de retirer le dernier administrateur.",
    "mail_alias_remove_failed": "Échec de la suppression de l'alias mail.",
    "user_import_missing_columns": "Colonnes manquantes dans le fichier CSV.",
    "user_import_bad_line": "Ligne invalide dans le fichier CSV.",
    "service_unknown": "Service inconnu.",
    "service_start_failed": "Échec du démarrage du service.",
    "service_stop_failed": "Échec de l'arrêt du service.",
    "service_restart_failed": "Échec du redémarrage du service.",
    "service_enable_failed": "Échec de l'activation du service au démarrage.",
    "service_disable_failed": "Échec de la désactivation du service au démarrage.",
    "upnp_port_open_failed": "Échec de l'ouverture du port via UPnP (routeur non compatible ou UPnP désactivé dessus).",
    "nftables_unavailable": "nftables n'est pas disponible sur ce serveur.",
    "app_unknown": "App inconnue.",
    "app_already_installed": "Cette app est déjà installée.",
    "app_install_failed": "L'installation a échoué.",
    "app_removed": "Cette app n'est plus installée.",
    "app_change_url_no_script": "Cette app ne supporte pas le changement d'URL.",
    "app_change_url_identical_domains": "Le domaine et le chemin sont identiques, rien à changer.",
    "app_upgrade_url_required": "Cette app doit être mise à jour manuellement (aucune source connue dans le catalogue).",
    "app_upgrade_app_already_up_to_date": "Cette app est déjà à jour.",
    "app_action_broken_parsing": "Les arguments fournis n'ont pas pu être interprétés.",
    "app_config_unable_to_apply": "La configuration n'a pas pu être appliquée.",
    "domain_unknown": "Domaine inconnu.",
    "certmanager_domain_cert_not_selfsigned": "Ce domaine a déjà un certificat valide (non auto-signé) — utilisez « forcer » pour le remplacer.",
    "certmanager_attempt_to_replace_valid_cert": "Ce domaine a déjà un certificat valide — utilisez « forcer » pour le remplacer.",
    "certmanager_attempt_to_renew_valid_cert": "Ce certificat est encore valide plus de 15 jours — utilisez « forcer » pour le renouveler quand même.",
    "certmanager_attempt_to_renew_nonLE_cert": "Ce domaine n'a pas de certificat Let's Encrypt à renouveler.",
    "certmanager_acme_not_configured_for_domain": "Le défi ACME n'est pas configuré pour ce domaine (vérifiez la config DNS/nginx).",
    "certmanager_domain_not_diagnosed_yet": "Ce domaine n'a pas encore été diagnostiqué — lancez d'abord un diagnostic complet.",
    "certmanager_domain_dns_ip_differs_from_public_ip": "L'IP DNS de ce domaine ne correspond pas à l'IP publique du serveur — le certificat ne peut pas être installé.",
    "certmanager_cert_install_success": "Certificat installé avec succès.",
    "main_domain_change_failed": "Le changement de domaine principal a échoué.",
    "domain_exists": "Ce domaine existe déjà.",
    "domain_cannot_remove_main": "Impossible de supprimer ce domaine : c'est le domaine principal. Définissez d'abord un autre domaine comme principal.",
    "domain_cannot_remove_main_add_new_one": "Impossible de supprimer ce domaine : c'est le domaine principal et le seul domaine existant. Ajoutez d'abord un autre domaine.",
    "domain_uninstall_app_first": "Des apps sont encore installées sur ce domaine — cochez « Supprimer aussi les apps installées » ou désinstallez-les d'abord.",
    "domain_dns_push_managed_in_parent_domain": "La configuration DNS automatique est gérée par le domaine parent — rien à faire ici.",
    "domain_dns_push_failed_to_authenticate": "Échec de l'authentification auprès du registrar — vérifiez les identifiants API dans la configuration du domaine.",
    "domain_registrar_is_not_configured": "Le registrar n'est pas encore configuré pour ce domaine (identifiants API absents) — la configuration DNS automatique n'est pas disponible.",
    "domain_dns_conf_special_use_tld": "Ce domaine utilise un TLD à usage spécial (ex. .local/.test) — il n'est pas censé avoir de vrais enregistrements DNS.",
}


def _current_user() -> str | None:
    return session.get("user")


def _wappos_api_admin_login(user: str, password: str) -> str:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/login",
        json={"user": user, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["token"]


def _wappos_api_admin_users(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/users",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_domains(token: str, full: bool = False) -> list[str]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/domains",
        params={"full": "true"} if full else None,
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_domain_detail(token: str, domain: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_domain_config(token: str, domain: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/config",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_domain_dns_suggest(token: str, domain: str) -> str:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/dns/suggest",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)
    return resp.json().get("suggestion", "")


_SPF_LINE_RE = re.compile(r'^(\S+)(\s+\d+\s+IN\s+TXT\s+)"(v=spf1[^"]*)"\s*$')
_DKIM_LINE_RE = re.compile(r'^mail\._domainkey\.(\S+)\s+\d+\s+IN\s+TXT\s+"v=DKIM1;')


def _augment_dns_suggestion_for_smtp_relay(raw: str, relay_host: str | None) -> tuple[str, bool]:
    if not relay_host or "smtp2go" not in relay_host.lower():
        return raw, False

    adjusted_lines: list[str] = []
    changed = False
    for line in raw.splitlines():
        spf_match = _SPF_LINE_RE.match(line)
        dkim_match = _DKIM_LINE_RE.match(line)
        if spf_match and "spf.smtp2go.com" not in spf_match.group(3):
            prefix, middle, spf_value = spf_match.groups()
            new_value = re.sub(r"\s*-all\s*$", " include:spf.smtp2go.com -all", spf_value)
            if new_value == spf_value:
                new_value = spf_value + " include:spf.smtp2go.com"
            adjusted_lines.append(f'{prefix}{middle}"{new_value}"')
            changed = True
        elif dkim_match:
            sub = dkim_match.group(1)
            adjusted_lines.append(f"; {line}")
            adjusted_lines.append(
                f"; ^ ignoré : DKIM signé en externe par SMTP2GO pour {sub}. "
                f"Remplacez par le CNAME de leur tableau de bord (Domains > DKIM), "
                f'ex. sXXXXXX._domainkey.{sub} 3600 IN CNAME dkim.smtp2go.net.'
            )
            changed = True
        else:
            adjusted_lines.append(line)
    return "\n".join(adjusted_lines), changed


def _wappos_api_set_domain_config(token: str, domain: str, panel_key: str, args: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/config/{panel_key}",
        json={"args": args},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)


def _wappos_api_run_domain_action(token: str, domain: str, action_id: str, args: str | None) -> None:
    payload: dict = {}
    if args:
        payload["args"] = args
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/actions/{action_id}",
        json=payload,
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)


def _wappos_api_set_main_domain(token: str, domain: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/main",
        headers={"X-Admin-Token": token},
        timeout=90,
    )
    _raise_for_status(resp)


def _wappos_api_install_domain_certificate(
    token: str, domain: str, force: bool = False, self_signed: bool = False, no_checks: bool = False
) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/cert",
        params={"force": force, "self_signed": self_signed, "no_checks": no_checks},
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)


def _wappos_api_renew_domain_certificate(
    token: str, domain: str, force: bool = False, email: bool = False, no_checks: bool = False
) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/cert/renew",
        params={"force": force, "email": email, "no_checks": no_checks},
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)


def _wappos_api_add_domain(
    token: str,
    domain: str,
    install_letsencrypt_cert: bool = False,
    dyndns_recovery_password: str | None = None,
    skip_dyndns_tos: bool = False,
) -> None:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/domains",
        json={
            "domain": domain,
            "install_letsencrypt_cert": install_letsencrypt_cert,
            "dyndns_recovery_password": dyndns_recovery_password,
            "skip_dyndns_tos": skip_dyndns_tos,
        },
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)


def _wappos_api_remove_domain(
    token: str, domain: str, remove_apps: bool = False, ignore_dyndns: bool = False
) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}",
        params={"remove_apps": remove_apps, "ignore_dyndns": ignore_dyndns},
        headers={"X-Admin-Token": token},
        timeout=120,
    )
    _raise_for_status(resp)


def _wappos_api_push_domain_dns(
    token: str, domain: str, dry_run: bool = True, force: bool = False, purge: bool = False
) -> dict:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/dns/push",
        params={"dry_run": dry_run, "force": force, "purge": purge},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_list_backups(token: str, human_readable: bool = True) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/backups",
        params={"with_info": True, "human_readable": human_readable},
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_backup_info(token: str, name: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/backups/{name}",
        params={"human_readable": True},
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_create_backup(
    token: str, name: str | None, description: str | None, system: list[str] | None, apps: list[str] | None
) -> dict:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/backups",
        json={"name": name, "description": description, "system": system, "apps": apps},
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_restore_backup(
    token: str, name: str, system: list[str] | None, apps: list[str] | None, force: bool
) -> dict:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/backups/{name}/restore",
        json={"system": system, "apps": apps, "force": force},
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_delete_backup(token: str, name: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/backups/{name}",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_versions(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/tools/versions",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_system_health(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/system/health",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_component_versions(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/system/wappos-versions",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_available_updates(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/tools/update",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_refresh_updates(token: str, target: str = "all") -> dict:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/update/{target}",
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_run_upgrade(token: str, target: str) -> dict:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/upgrade/{target}",
        headers={"X-Admin-Token": token},
        timeout=320,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_regen_conf(token: str, dry_run: bool = False, force: bool = False) -> dict:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/regenconf",
        json={"dry_run": dry_run, "force": force, "with_diff": True},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)
    return resp.json() if resp.content else {}


def _wappos_api_change_root_password(token: str, new_password: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/rootpw",
        json={"new_password": new_password},
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_reboot(token: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/reboot",
        params={"force": "true"},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_shutdown(token: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/tools/shutdown",
        params={"force": "true"},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_services(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/services",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_service_detail(token: str, name: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/services/{name}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_service_action(token: str, name: str, action: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/services/{name}/{action}",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_service_log(token: str, name: str, number: int = 50) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/services/{name}/log",
        params={"number": number},
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_logs(token: str, limit: int = 25) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/logs",
        params={"limit": limit},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_log_detail(token: str, name: str, number: int = 25) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/logs/{name}",
        params={"number": number},
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_firewall(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/firewall",
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_open_firewall_port(token: str, protocol: str, port, comment: str = "", upnp: bool = False) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/firewall/{protocol}/{port}/open",
        params={"comment": comment, "upnp": upnp},
        headers={"X-Admin-Token": token},
        timeout=50 if upnp else 15,
    )
    _raise_for_status(resp)


def _wappos_api_close_firewall_port(token: str, protocol: str, port, upnp_only: bool = False) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/firewall/{protocol}/{port}/close",
        params={"upnp_only": upnp_only},
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)


def _wappos_api_set_upnp(token: str, enabled: bool) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/firewall/upnp/{'true' if enabled else 'false'}",
        headers={"X-Admin-Token": token},
        timeout=50,
    )
    _raise_for_status(resp)


def _wappos_api_admin_apps(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_app_detail(token: str, app_id: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_install_app(token: str, app_id: str, label: str | None, args: str, force: bool = False) -> dict:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/apps",
        json={"app": app_id, "label": label or None, "args": args or None, "force": force},
        headers={"X-Admin-Token": token},
        timeout=300,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_remove_app(token: str, app_id: str, purge: bool) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}",
        params={"purge": purge},
        headers={"X-Admin-Token": token},
        timeout=120,
    )
    _raise_for_status(resp)


def _wappos_api_upgrade_app(token: str, app_id: str, force: bool = False) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/upgrade",
        params={"force": force},
        headers={"X-Admin-Token": token},
        timeout=300,
    )
    _raise_for_status(resp)


def _wappos_api_change_app_url(token: str, app_id: str, domain: str, path: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/changeurl",
        json={"domain": domain, "path": path},
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_change_app_label(token: str, app_id: str, new_label: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/label",
        json={"new_label": new_label},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_dismiss_app_notification(token: str, app_id: str, name: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/dismiss_notification/{name}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_app_map(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/map",
        params={"raw": "true"},
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_get_app_setting(token: str, app_id: str, key: str) -> str | None:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/setting",
        params={"key": key},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json().get("value")


def _wappos_api_set_app_setting(token: str, app_id: str, key: str, value: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/setting",
        json={"key": key, "value": value},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_delete_app_setting(token: str, app_id: str, key: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/setting",
        params={"key": key},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_domain_url_available(token: str, domain: str, path: str) -> bool:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/domains/{domain}/urlavailable",
        params={"path": path},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return bool(resp.json().get("available"))


def _wappos_api_app_catalog(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/catalog",
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_app_manifest(token: str, app_id: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/manifest",
        params={"app_id": app_id},
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_app_actions(token: str, app_id: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/actions",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_run_app_action(token: str, app_id: str, action_id: str, args: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/actions/{action_id}",
        json={"args": args or None},
        headers={"X-Admin-Token": token},
        timeout=120,
    )
    _raise_for_status(resp)


def _wappos_api_app_config(token: str, app_id: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/config",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_set_app_config(token: str, app_id: str, panel_key: str, args: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/apps/{app_id}/config/{panel_key}",
        json={"args": args},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)


def _wappos_api_settings(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/settings",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_set_settings(token: str, panel_key: str, args: str) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/settings/{panel_key}",
        json={"args": args},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)


def _wappos_api_reset_setting(token: str, key: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/settings/{key}",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_reset_all_settings(token: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/settings",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)


def _wappos_api_admin_permissions(token: str) -> dict[str, dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/permissions",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_admin_groups(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/groups",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_update_permission(token: str, permission: str, add=None, remove=None) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/permissions/{permission}",
        json={"add": add, "remove": remove},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_create_group(token: str, groupname: str) -> None:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/groups",
        json={"groupname": groupname},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_delete_group(token: str, groupname: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/groups/{groupname}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_update_group_members(token: str, groupname: str, add=None, remove=None) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/groups/{groupname}/members",
        json={"add": add, "remove": remove},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_admin_diagnosis(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/diagnosis",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_diagnosis_categories(token: str) -> list[str]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/diagnosis/categories",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_admin_run_diagnosis(token: str, category: str | None = None) -> list[dict]:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/diagnosis/run",
        params={"category": category} if category else None,
        headers={"X-Admin-Token": token},
        timeout=150,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_diagnosis_share(token: str) -> str:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/diagnosis/share",
        headers={"X-Admin-Token": token},
        timeout=30,
    )
    _raise_for_status(resp)
    return resp.json()["url"]


def _wappos_api_diagnosis_set_ignored(token: str, category: str, meta: dict, ignored: bool) -> list[dict]:
    action = "ignore" if ignored else "unignore"
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/diagnosis/{category}/{action}",
        json={"meta": meta},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_storage_disks(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/storage/disks",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_storage_mounts(token: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/storage/mounts",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_disk_smart(token: str, name: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/storage/disks/{name}/smart",
        headers={"X-Admin-Token": token},
        timeout=15,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_create_user(token: str, **fields) -> None:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/users",
        json=fields,
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_update_user(token: str, username: str, **fields) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/users/{username}",
        json=fields,
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_delete_user(token: str, username: str, purge: bool = False) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/users/{username}",
        params={"purge": purge},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_export_users_csv(token: str) -> bytes:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/users/export",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.content


def _wappos_api_import_users_csv(token: str, filename: str, content: bytes, update: bool, delete: bool) -> dict:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/users/import",
        files={"csvfile": (filename, content, "text/csv")},
        data={"update": str(update).lower(), "delete": str(delete).lower()},
        headers={"X-Admin-Token": token},
        timeout=60,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_user_detail(token: str, username: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/users/{username}",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_list_ssh_keys(token: str, username: str) -> list[dict]:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/admin/users/{username}/ssh-keys",
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_add_ssh_key(token: str, username: str, key: str, comment: str | None = None) -> None:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/admin/users/{username}/ssh-keys",
        json={"key": key, "comment": comment},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_remove_ssh_key(token: str, username: str, key: str) -> None:
    resp = requests.delete(
        f"{WAPPOS_API_BASE}/admin/users/{username}/ssh-keys",
        json={"key": key},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_update_permission_properties(token: str, permission: str, **fields) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/permissions/{permission}/properties",
        json=fields,
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_update_permission_logo(token: str, permission: str, filename: str, content: bytes) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/admin/permissions/{permission}/logo",
        files={"logo": (filename, content, "image/png")},
        headers={"X-Admin-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _is_wappos_infra_app(app_id: str) -> bool:
    return app_id.startswith("wappos_")


def _dedupe_by(items, key):
    seen = set()
    result = []
    for item in items:
        k = key(item)
        if k in seen:
            continue
        seen.add(k)
        result.append(item)
    return result


def _login_or_401():
    user = _current_user()
    if not user:
        return None, None
    return user, session.get("token")


def _error_message(exc: requests.exceptions.HTTPError) -> str:
    try:
        detail = exc.response.json().get("detail", {})
    except (ValueError, AttributeError):
        detail = {}
    code = detail.get("code")
    if code in _ERROR_MESSAGES:
        return _ERROR_MESSAGES[code]
    native_detail = detail.get("native_detail")
    if native_detail:
        return _wappos_rebrand(native_detail)
    return "L'action a échoué (l'API Wappos a refusé la requête)."


def _build_args_from_options(options: list[dict], form, files=None) -> str:
    files = files or {}
    pairs = []
    for o in options:
        if o.get("type") == "button":
            continue
        oid = o.get("id")
        if not oid:
            continue
        if o.get("type") == "boolean":
            pairs.append((oid, "1" if form.get(oid) else "0"))
        elif o.get("type") == "file":
            uploaded = files.get(f"{oid}__upload")
            if uploaded and uploaded.filename:
                content = uploaded.read()
                pairs.append((oid, base64.b64encode(content).decode("ascii")))
            elif form.get(f"{oid}__remove"):
                pairs.append((oid, ""))
        elif o.get("type") == "password":
            if form.get(oid):
                pairs.append((oid, form.get(oid, "")))
        elif o.get("type") == "tags" and o.get("choices"):
            pairs.append((oid, ",".join(form.getlist(oid))))
        elif oid in form:
            pairs.append((oid, form.get(oid, "")))
    return urlencode(pairs)


def _redirect_with_message(*, message: str | None = None, error: str | None = None):
    target = url_for("index")
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


def _failed_system_units() -> list[str] | None:
    try:
        result = subprocess.run(
            ["systemctl", "list-units", "--all", "--state=failed", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        app.logger.error("Dashboard: failed to list failed units: %s", e)
        return None
    units = []
    for line in result.stdout.splitlines():
        parts = line.split(None, 1)
        if parts:
            units.append(parts[0])
    return units


def _systemd_timestamp_to_epoch(value: str) -> float | None:
    if not value:
        return None
    try:
        result = subprocess.run(
            ["date", "-d", value, "+%s"], capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def _failed_system_units_detail() -> list[dict] | None:
    names = _failed_system_units()
    if names is None:
        return None
    units = []
    for name in names:
        entry = {"name": name, "result": "unknown", "since": None}
        try:
            result = subprocess.run(
                ["systemctl", "show", name, "--property=Result", "--property=ActiveEnterTimestamp", "--value"],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            app.logger.error("Failed to inspect unit %r: %s", name, e)
            units.append(entry)
            continue
        lines = result.stdout.splitlines()
        if len(lines) >= 1 and lines[0]:
            entry["result"] = lines[0]
        if len(lines) >= 2 and lines[1]:
            entry["since"] = _systemd_timestamp_to_epoch(lines[1])
        units.append(entry)
    return units


_STANDALONE_SERVICES = (
    ("wappos_admin", "Wappos Admin"),
    ("wappos_portal", "Wappos Portal"),
    ("wappos_api", "Wappos API"),
    ("prometheus", "Prometheus"),
)


def _standalone_services_status() -> list[dict]:
    services = []
    for unit_name, label in _STANDALONE_SERVICES:
        entry = {"name": unit_name, "label": label, "installed": False, "status": "unknown", "since": None}
        try:
            result = subprocess.run(
                ["systemctl", "show", f"{unit_name}.service",
                 "--property=LoadState", "--property=ActiveState", "--property=SubState",
                 "--property=ActiveEnterTimestamp", "--value"],
                capture_output=True, text=True, timeout=10,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            app.logger.error("Failed to inspect standalone service %r: %s", unit_name, e)
            services.append(entry)
            continue
        lines = result.stdout.splitlines()
        load_state = lines[0] if len(lines) >= 1 else ""
        if load_state != "not-found":
            entry["installed"] = True
            entry["status"] = lines[2] if len(lines) >= 3 and lines[2] else (lines[1] if len(lines) >= 2 else "unknown")
            if len(lines) >= 4 and lines[3]:
                entry["since"] = _systemd_timestamp_to_epoch(lines[3])
        services.append(entry)
    return services


def _dashboard_load_mounts(token: str) -> dict:
    mounts = _wappos_api_storage_mounts(token)
    return {"mounts": sorted(mounts, key=lambda m: len(m.get("mountpoint", "")))}


def _dashboard_load_services(token: str) -> dict:
    services = _wappos_api_services(token)
    return {
        "services_total": len(services),
        "services_down": sum(1 for s in services if s.get("status") not in ("running", "exited")),
    }


def _dashboard_load_diagnosis(token: str) -> dict:
    reports = _wappos_api_admin_diagnosis(token)
    return {
        "diag_errors": sum(r.get("error_count", 0) for r in reports),
        "diag_warnings": sum(r.get("warning_count", 0) for r in reports),
    }


def _dashboard_load_last_backup(token: str) -> dict:
    result = _wappos_api_list_backups(token)
    archives = result.get("archives", {})
    last_backup = None
    if archives:
        latest = list(archives.values())[-1]
        last_backup = latest.get("created_at") if isinstance(latest, dict) else None
    return {"last_backup": last_backup}


def _dashboard_load_updates(token: str) -> dict:
    updates = _wappos_api_available_updates(token)
    return {
        "app_updates": len(updates.get("apps", [])),
        "system_update_categories": len(updates.get("system", {})),
    }


_DASHBOARD_LOADERS = {
    "mounts": _dashboard_load_mounts,
    "services": _dashboard_load_services,
    "diagnosis": _dashboard_load_diagnosis,
    "last_backup": _dashboard_load_last_backup,
    "updates": _dashboard_load_updates,
}
_DASHBOARD_MAX_CONCURRENT_REQUESTS = 3


def _dashboard_summary(token: str) -> dict:
    summary = {
        "mounts": None,
        "services_down": None,
        "services_total": None,
        "diag_errors": None,
        "diag_warnings": None,
        "last_backup": None,
        "app_updates": None,
        "system_update_categories": None,
        "failed_units": None,
    }

    with ThreadPoolExecutor(max_workers=_DASHBOARD_MAX_CONCURRENT_REQUESTS) as executor:
        futures = {name: executor.submit(loader, token) for name, loader in _DASHBOARD_LOADERS.items()}
        failed_units_future = executor.submit(_failed_system_units)

        for name, future in futures.items():
            try:
                summary.update(future.result())
            except requests.exceptions.RequestException as e:
                app.logger.error("Dashboard: failed to load %s: %s", name, e)

        summary["failed_units"] = failed_units_future.result()

    return summary


@app.route("/")
def home():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    dashboard = _dashboard_summary(token)
    return render_template(
        "home.html", user=user, app_version=APP_VERSION, year=datetime.now().year, dashboard=dashboard,
    )


@app.route("/tools")
def tools_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    return render_template("tools_home.html", user=user, app_version=APP_VERSION)


@app.route("/users")
def index():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        users = [u for u in _wappos_api_admin_users(token) if u.get("username") not in _HIDDEN_SYSTEM_USERS]
        domains = _wappos_api_domains(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load admin data for %r: %s", user, e)
        return render_template(
            "users.html", user=user, users=[], domains=[], error="L'API Wappos est injoignable.",
            message=None, app_version=APP_VERSION,
        ), 503

    return render_template(
        "users.html", user=user, users=users, domains=domains,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


def _redirect_to_apps(*, message: str | None = None, error: str | None = None):
    target = url_for("apps")
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


@app.route("/apps")
def apps():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        installed_apps = _wappos_api_admin_apps(token)
        docker_gate_app_ids = docker_gate.get_all_yunohost_app_ids()
        installed_apps = [
            a for a in installed_apps
            if not _is_wappos_infra_app(a.get("id", "")) and a.get("id") not in docker_gate_app_ids
        ]
        raw_permissions = _wappos_api_admin_permissions(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load apps for %r: %s", user, e)
        return render_template(
            "apps.html", user=user, apps=[], error="L'API Wappos est injoignable.",
            app_version=APP_VERSION,
        ), 503

    for a in installed_apps:
        a["permissions"] = [
            {"id": pid, **data} for pid, data in sorted(raw_permissions.items()) if pid.startswith(f"{a['id']}.")
        ]
        main_permission = raw_permissions.get(f"{a['id']}.main", {})
        a["logo_hash"] = a.get("logo") or main_permission.get("logo_hash")

    return render_template(
        "apps.html", user=user, apps=installed_apps,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/apps/<app_id>")
def app_detail(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    docker_entry = docker_gate.get_app_entry_by_yunohost_id(app_id)
    if docker_entry:
        return redirect(url_for("docker_apps", msg=f"{docker_entry['slug']} est une app Docker Gate — gérée depuis cette page."))

    try:
        detail = _wappos_api_app_detail(token, app_id)
        domains = _wappos_api_domains(token, full=True)
        config = _wappos_api_app_config(token, app_id) if detail.get("supports_config_panel") else None
        all_permissions = _wappos_api_admin_permissions(token)
        app_permissions = {
            pid: p for pid, p in all_permissions.items() if pid.startswith(f"{app_id}.")
        }
        groups = _wappos_api_admin_groups(token)
        _rebrand_app_detail_text(detail)
        if config:
            _rebrand_config_panels(config.get("panels", []))
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load app detail for %r/%r: %s", user, app_id, e)
        return render_template(
            "app_detail.html", user=user, detail=None, domains=[], config=None,
            app_permissions={}, groups=[],
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    raw_setting_key = request.args.get("setting_key")
    raw_setting_value = None
    if raw_setting_key:
        try:
            raw_setting_value = _wappos_api_get_app_setting(token, app_id, raw_setting_key)
        except requests.exceptions.HTTPError as e:
            return render_template(
                "app_detail.html", user=user, detail=detail, domains=domains, config=config,
                app_permissions=app_permissions, groups=groups,
                raw_setting_key=raw_setting_key, raw_setting_value=None,
                error=_error_message(e), app_version=APP_VERSION,
            )

    return render_template(
        "app_detail.html", user=user, detail=detail, domains=domains, config=config,
        app_permissions=app_permissions, groups=groups,
        raw_setting_key=raw_setting_key, raw_setting_value=raw_setting_value,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/apps/<app_id>/setting/set", methods=["POST"])
def app_setting_set(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    key = (request.form.get("key") or "").strip()
    value = request.form.get("value") or ""
    if not key:
        return _redirect_to_app_detail(app_id, error="La clé de réglage ne peut pas être vide.")
    try:
        _wappos_api_set_app_setting(token, app_id, key, value)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return redirect(url_for("app_detail", app_id=app_id, setting_key=key, msg=f"Réglage « {key} » mis à jour."))


@app.route("/apps/<app_id>/setting/delete", methods=["POST"])
def app_setting_delete(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    key = (request.form.get("key") or "").strip()
    if not key:
        return _redirect_to_app_detail(app_id, error="La clé de réglage ne peut pas être vide.")
    try:
        _wappos_api_delete_app_setting(token, app_id, key)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message=f"Réglage « {key} » supprimé.")


def _redirect_to_app_detail(app_id: str, *, message: str | None = None, error: str | None = None):
    target = url_for("app_detail", app_id=app_id)
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


def _native_apps_fallback(app_id: str, *, message: str | None = None, error: str | None = None):
    return _redirect_to_apps(message=message, error=error)


def _redirect_to_app_management(app_id: str, *, native_fallback, message: str | None = None, error: str | None = None):
    docker_entry = docker_gate.get_app_entry_by_yunohost_id(app_id)
    if docker_entry:
        target = url_for("docker_edit", slug=docker_entry["slug"])
        if message:
            target += f"?msg={quote(message)}"
        elif error:
            target += f"?error={quote(error)}"
        return redirect(target)
    return native_fallback(app_id, message=message, error=error)


@app.route("/apps/<app_id>/upgrade", methods=["POST"])
def app_upgrade_action(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    force = request.form.get("force") == "1"
    try:
        _wappos_api_upgrade_app(token, app_id, force=force)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message="Mise à jour lancée.")


@app.route("/apps/<app_id>/changeurl", methods=["POST"])
def app_changeurl_action(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    domain = request.form.get("domain", "").strip()
    raw_path = request.form.get("path", "").strip()
    if not domain or not raw_path:
        return _redirect_to_app_detail(app_id, error="Domaine et chemin requis.")
    path = "/" + raw_path.lstrip("/")
    try:
        _wappos_api_change_app_url(token, app_id, domain, path)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message="URL modifiée.")


@app.route("/apps/<app_id>/label", methods=["POST"])
def app_label_action(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    new_label = request.form.get("new_label", "").strip()
    if not new_label:
        return _redirect_to_app_detail(app_id, error="Le libellé ne peut pas être vide.")
    try:
        _wappos_api_change_app_label(token, app_id, new_label)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message="Libellé modifié.")


@app.route("/apps/<app_id>/dismiss/<name>", methods=["POST"])
def app_dismiss_notification_action(app_id: str, name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_dismiss_app_notification(token, app_id, name)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id)


@app.route("/apps/<app_id>/remove", methods=["POST"])
def app_remove_action(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    purge = request.form.get("purge") == "1"

    docker_entry = docker_gate.get_app_entry_by_yunohost_id(app_id)
    if docker_entry:
        def _remove_app(aid):
            _wappos_api_remove_app(token, aid, purge)

        try:
            warnings = docker_gate.remove_docker_app(
                docker_entry["slug"], delete_data=purge, delete_domain=False,
                remove_app_fn=_remove_app,
            )
        except docker_gate.DockerGateError as e:
            return _redirect_to_app_detail(app_id, error=str(e))
        for w in warnings:
            app.logger.warning("Docker app removal warning (%s): %s", docker_entry["slug"], w)
        return _redirect_to_apps(message="App désinstallée.")

    try:
        _wappos_api_remove_app(token, app_id, purge)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_apps(message="App désinstallée.")


@app.route("/apps/<app_id>/config/<panel_key>", methods=["POST"])
def app_config_submit(app_id: str, panel_key: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    section_id = request.form.get("__section_id__")
    try:
        config = _wappos_api_app_config(token, app_id)
        options = [
            o
            for panel in config.get("panels", [])
            if panel.get("id") == panel_key
            for section in panel.get("sections", [])
            if section.get("id") == section_id
            for o in section.get("options", [])
        ]
        args = _build_args_from_options(options, request.form, request.files)
        _wappos_api_set_app_config(token, app_id, panel_key, args)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message="Configuration appliquée.")


@app.route("/apps/<app_id>/actions/<action_id>", methods=["POST"])
def app_action_submit(app_id: str, action_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        config = _wappos_api_app_config(token, app_id)
        panel_id, section_id, _button_id = action_id.split(".", 2)
        options = [
            o
            for panel in config.get("panels", [])
            if panel.get("id") == panel_id
            for section in panel.get("sections", [])
            if section.get("id") == section_id
            for o in section.get("options", [])
        ]
        args = _build_args_from_options(options, request.form, request.files)
        _wappos_api_run_app_action(token, app_id, action_id, args)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_detail(app_id, error=_error_message(e))
    return _redirect_to_app_detail(app_id, message="Action exécutée.")


_APP_QUALITY_FILTERS = {
    "highQuality": lambda a: a["high_quality"],
    "decentQuality": lambda a: a["decent_quality"],
    "working": lambda a: a["working"],
    "all": lambda a: True,
}


@app.route("/apps/catalog")
def app_catalog_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    search = request.args.get("q", "").strip().lower()
    category = request.args.get("category") or None
    subtag = request.args.get("subtag") or "all"
    quality = request.args.get("quality") or "decentQuality"
    try:
        data = _wappos_api_app_catalog(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load app catalog for %r: %s", user, e)
        return render_template(
            "app_catalog.html", user=user, apps=[], categories=[], show_categories=True,
            current_category=None, search=search, category="", subtag=subtag, quality=quality,
            antifeatures_by_id={}, error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    categories = data.get("categories", [])
    apps = data.get("apps", [])
    for c in categories:
        if c.get("description"):
            c["description"] = _wappos_rebrand(c["description"])
    for a in apps:
        if a.get("description"):
            a["description"] = _wappos_rebrand(a["description"])

    for a in apps:
        a["working"] = a.get("state") == "working"
        a["decent_quality"] = a["working"] and (a.get("level") or -1) > 4
        a["high_quality"] = a["working"] and (a.get("level") or -1) >= 8

    apps = [a for a in apps if _APP_QUALITY_FILTERS.get(quality, _APP_QUALITY_FILTERS["decentQuality"])(a)]

    show_categories = not search and not category
    if not show_categories:
        if category and category != "all":
            apps = [a for a in apps if a.get("category") == category]
            if subtag and subtag != "all":
                if subtag == "others":
                    apps = [a for a in apps if not a.get("subtags")]
                else:
                    apps = [a for a in apps if subtag in (a.get("subtags") or [])]
        if search:
            apps = [
                a for a in apps
                if search in a["id"].lower() or search in a["name"].lower() or search in a.get("description", "").lower()
            ]
        apps.sort(key=lambda a: a["name"].lower())

    current_category = next((c for c in categories if c["id"] == category), None)
    antifeatures_by_id = {af["id"]: af for af in data.get("antifeatures", [])}

    return render_template(
        "app_catalog.html", user=user, apps=apps, categories=categories,
        show_categories=show_categories, current_category=current_category,
        search=search, category=category or "", subtag=subtag, quality=quality,
        antifeatures_by_id=antifeatures_by_id, app_version=APP_VERSION,
    )


@app.route("/apps/install-custom", methods=["POST"])
def app_install_custom():
    user, _ = _login_or_401()
    if not user:
        return "Unauthorized", 401
    url = request.form.get("url", "").strip()
    if not url:
        return redirect(url_for("app_catalog_page"))
    return redirect(url_for("app_install_form", app_id=url))


@app.route("/apps/install/<path:app_id>")
def app_install_form(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        manifest = _wappos_api_app_manifest(token, app_id)
        if manifest.get("description"):
            manifest["description"] = _wappos_rebrand(manifest["description"])
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load manifest for %r/%r: %s", user, app_id, e)
        return render_template(
            "app_install.html", user=user, manifest=None,
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    antifeatures = []
    potential_alternative_to = []
    try:
        catalog = _wappos_api_app_catalog(token)
        entry = next((a for a in catalog.get("apps", []) if a.get("id") == app_id), None)
        if entry:
            antifeatures_by_id = {af["id"]: af for af in catalog.get("antifeatures", [])}
            antifeatures = [antifeatures_by_id.get(af_id, {"id": af_id, "title": af_id}) for af_id in entry.get("antifeatures", [])]
            potential_alternative_to = entry.get("potential_alternative_to", [])
    except requests.exceptions.RequestException:
        pass

    return render_template(
        "app_install.html", user=user, manifest=manifest,
        antifeatures=antifeatures, potential_alternative_to=potential_alternative_to,
        error=request.args.get("error"), app_version=APP_VERSION,
    )


@app.route("/apps/install/<path:app_id>", methods=["POST"])
def app_install_submit(app_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    label = request.form.get("label", "").strip() or None
    force = request.form.get("force") == "on"
    try:
        manifest = _wappos_api_app_manifest(token, app_id)
        args = _build_args_from_options(manifest.get("install", []), request.form, request.files)
        _wappos_api_install_app(token, app_id, label, args, force=force)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("app_install_form", app_id=app_id, error=_error_message(e)))
    return _redirect_to_apps(message=f"« {label or app_id} » installée.")


def _redirect_to_groups(*, message: str | None = None, error: str | None = None):
    target = url_for("groups")
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


@app.route("/groups")
def groups():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        raw_groups = _wappos_api_admin_groups(token)
        raw_permissions = _wappos_api_admin_permissions(token)
        usernames = {u["username"] for u in _wappos_api_admin_users(token)}
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load groups for %r: %s", user, e)
        return render_template(
            "groups.html", user=user, primary_groups=[], user_groups=[],
            permission_options=[], user_options=[],
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    permission_options = sorted(
        (
            {"id": pid, "label": data["label"]}
            for pid, data in raw_permissions.items()
            if data.get("url") or data.get("protected")
        ),
        key=lambda p: p["label"],
    )
    user_options = sorted(usernames)

    primary_groups = sorted(
        (g for g in raw_groups if g["name"] not in usernames), key=lambda g: g["name"]
    )
    user_groups = sorted(
        (g for g in raw_groups if g["name"] in usernames), key=lambda g: g["name"]
    )

    return render_template(
        "groups.html", user=user, primary_groups=primary_groups, user_groups=user_groups,
        permission_options=permission_options, user_options=user_options,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/groups", methods=["POST"])
def create_group():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    groupname = request.form.get("groupname", "").strip()
    if not groupname:
        return _redirect_to_groups(error="Le nom du groupe ne peut pas être vide.")

    try:
        _wappos_api_create_group(token, groupname)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Create group %r failed: %s", groupname, e)
        return _redirect_to_groups(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Create group %r failed: %s", groupname, e)
        return _redirect_to_groups(error="L'API Wappos est injoignable.")

    return _redirect_to_groups(message=f"Groupe {groupname} créé.")


@app.route("/groups/<groupname>/delete", methods=["POST"])
def delete_group(groupname: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        _wappos_api_delete_group(token, groupname)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Delete group %r failed: %s", groupname, e)
        return _redirect_to_groups(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Delete group %r failed: %s", groupname, e)
        return _redirect_to_groups(error="L'API Wappos est injoignable.")

    return _redirect_to_groups(message=f"Groupe {groupname} supprimé.")


@app.route("/groups/<groupname>/members", methods=["POST"])
def update_group_members(groupname: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    desired_members = set(request.form.getlist("members"))

    try:
        current = next((g for g in _wappos_api_admin_groups(token) if g["name"] == groupname), None)
        current_members = set(current["members"]) if current else set()
        to_add = list(desired_members - current_members)
        to_remove = list(current_members - desired_members)
        _wappos_api_update_group_members(token, groupname, add=to_add or None, remove=to_remove or None)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Update members of group %r failed: %s", groupname, e)
        return _redirect_to_groups(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Update members of group %r failed: %s", groupname, e)
        return _redirect_to_groups(error="L'API Wappos est injoignable.")

    return _redirect_to_groups(message=f"Membres du groupe {groupname} mis à jour.")


@app.route("/groups/<groupname>/permissions", methods=["POST"])
def update_group_permissions(groupname: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    desired_permissions = set(request.form.getlist("permissions"))
    locked_permissions = set(request.form.getlist("locked"))

    try:
        current = next((g for g in _wappos_api_admin_groups(token) if g["name"] == groupname), None)
        current_permissions = set(current["permissions"]) if current else set()
        to_add = (desired_permissions - current_permissions) - locked_permissions
        to_remove = (current_permissions - desired_permissions) - locked_permissions
        for permission in to_add:
            _wappos_api_update_permission(token, permission, add=[groupname])
        for permission in to_remove:
            _wappos_api_update_permission(token, permission, remove=[groupname])
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Update permissions of group %r failed: %s", groupname, e)
        return _redirect_to_groups(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Update permissions of group %r failed: %s", groupname, e)
        return _redirect_to_groups(error="L'API Wappos est injoignable.")

    return _redirect_to_groups(message=f"Permissions du groupe {groupname} mises à jour.")


@app.route("/permissions/<path:permission>/groups", methods=["POST"])
def update_permission_groups(permission: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    app_id = permission.split(".", 1)[0]

    desired_groups = set(request.form.getlist("groups"))
    locked_groups = set(request.form.getlist("locked"))

    try:
        current = _wappos_api_admin_permissions(token).get(permission, {})
        current_groups = set(current.get("allowed", []))
        to_add = list((desired_groups - current_groups) - locked_groups)
        to_remove = list((current_groups - desired_groups) - locked_groups)
        if to_add or to_remove:
            _wappos_api_update_permission(token, permission, add=to_add or None, remove=to_remove or None)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_app_management(app_id, native_fallback=_redirect_to_app_detail, error=_error_message(e))
    except requests.exceptions.RequestException:
        return _redirect_to_app_management(app_id, native_fallback=_redirect_to_app_detail, error="L'API Wappos est injoignable.")

    return _redirect_to_app_management(app_id, native_fallback=_redirect_to_app_detail, message=f"Accès de « {permission} » mis à jour.")


@app.route("/permissions/<path:permission>/properties", methods=["POST"])
def update_permission_properties(permission: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    app_id = permission.split(".", 1)[0]

    label = request.form.get("label", "").strip() or None
    description = request.form.get("description", "").strip() or None
    order = request.form.get("order", "").strip()
    show_tile = request.form.get("show_tile") == "on"
    hide_from_public = request.form.get("hide_from_public") == "on"

    fields = {
        "label": label,
        "description": description,
        "order": int(order) if order else None,
        "show_tile": show_tile,
        "hide_from_public": hide_from_public,
    }

    logo = request.files.get("logo")

    try:
        _wappos_api_update_permission_properties(token, permission, **fields)
        if logo and logo.filename:
            _wappos_api_update_permission_logo(token, permission, logo.filename, logo.read())
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Update properties of permission %r failed: %s", permission, e)
        return _redirect_to_app_management(app_id, native_fallback=_native_apps_fallback, error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Update properties of permission %r failed: %s", permission, e)
        return _redirect_to_app_management(app_id, native_fallback=_native_apps_fallback, error="L'API Wappos est injoignable.")

    try:
        refreshed = _wappos_api_admin_permissions(token).get(permission, {})
    except requests.exceptions.RequestException:
        refreshed = {}
    if show_tile and refreshed.get("show_tile") is False:
        return _redirect_to_app_management(
            app_id, native_fallback=_native_apps_fallback,
            error=f"Propriétés de {permission} mises à jour, mais « Afficher la tuile » n'a pas pu être "
            "activé (Wappos l'ignore pour une permission sans URL)."
        )
    return _redirect_to_app_management(app_id, native_fallback=_native_apps_fallback, message=f"Propriétés de {permission} mises à jour.")


@app.route("/users/export")
def export_users():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        csv_content = _wappos_api_export_users_csv(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Export users failed for %r: %s", user, e)
        return _redirect_with_message(error="L'API Wappos est injoignable.")

    return Response(
        csv_content, mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=users.csv"},
    )


@app.route("/users/import", methods=["POST"])
def import_users():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    csvfile = request.files.get("csvfile")
    if not csvfile or not csvfile.filename:
        return _redirect_with_message(error="Aucun fichier CSV fourni.")

    update = request.form.get("update") == "on"
    delete = request.form.get("delete") == "on"

    try:
        result = _wappos_api_import_users_csv(token, csvfile.filename, csvfile.read(), update=update, delete=delete)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Import users failed: %s", e)
        return _redirect_with_message(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Import users failed: %s", e)
        return _redirect_with_message(error="L'API Wappos est injoignable.")

    created = result.get("created", 0)
    updated = result.get("updated", 0)
    deleted = result.get("deleted", 0)
    errors = result.get("errors", 0)
    summary = f"{created} créé(s), {updated} mis à jour, {deleted} supprimé(s)"
    if errors:
        summary += f", {errors} en échec"
        if created + updated + deleted == 0:
            return _redirect_with_message(error=f"Import échoué : {summary}.")
        return _redirect_with_message(error=f"Import partiellement réussi : {summary}.")
    return _redirect_with_message(message=f"Import réussi : {summary}.")


def _quota_limit_to_number(limit: str) -> int:
    match = re.match(r"^(\d+)", limit)
    return int(match.group(1)) if match else 0


@app.route("/users/<username>/edit")
def edit_user(username: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        detail = _wappos_api_user_detail(token, username)
        ssh_keys = _wappos_api_list_ssh_keys(token, username)
        domains = _wappos_api_domains(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load user detail for %r: %s", username, e)
        return redirect(url_for("index", error="L'API Wappos est injoignable."))

    detail["mailbox_quota_numeric"] = _quota_limit_to_number(detail["mailbox_quota_limit"])

    return render_template(
        "user_edit.html", user=user, detail=detail, ssh_keys=ssh_keys, domains=domains,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/users/<username>/ssh-keys/add", methods=["POST"])
def add_ssh_key(username: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    key = request.form.get("key", "").strip()
    comment = request.form.get("comment", "").strip() or None
    if not key:
        return redirect(url_for("edit_user", username=username, error="La clé SSH ne peut pas être vide."))
    if "\n" in key or "\r" in key:
        return redirect(url_for(
            "edit_user", username=username,
            error="Une seule clé SSH à la fois (pas de saut de ligne).",
        ))
    if not re.match(r"^(ssh-ed25519|ssh-rsa|ecdsa-sha2-\S+|sk-ssh-ed25519@openssh\.com) [A-Za-z0-9+/]+=*( .*)?$", key):
        return redirect(url_for(
            "edit_user", username=username,
            error="Format de clé SSH non reconnu (attendu : type + clé en base64).",
        ))
    try:
        _wappos_api_add_ssh_key(token, username, key, comment=comment)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("edit_user", username=username, error=_error_message(e)))
    return redirect(url_for("edit_user", username=username, msg="Clé SSH ajoutée."))


@app.route("/users/<username>/ssh-keys/remove", methods=["POST"])
def remove_ssh_key(username: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    key = request.form.get("key", "")
    try:
        _wappos_api_remove_ssh_key(token, username, key)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("edit_user", username=username, error=_error_message(e)))
    return redirect(url_for("edit_user", username=username, msg="Clé SSH supprimée."))


@app.route("/users/<username>/edit", methods=["POST"])
def update_user_detail(username: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    fullname = request.form.get("fullname", "").strip()
    mail = request.form.get("mail", "").strip()
    mail_confirm = request.form.get("mail_confirm", "").strip()
    mailbox_quota_numeric = request.form.get("mailbox_quota", "").strip()
    change_password = request.form.get("change_password", "")
    change_password_confirm = request.form.get("change_password_confirm", "")

    if mail != mail_confirm:
        return redirect(url_for("edit_user", username=username, error="Les adresses email ne correspondent pas."))
    if change_password != change_password_confirm:
        return redirect(url_for("edit_user", username=username, error="Les mots de passe ne correspondent pas."))

    mailbox_quota = f"{mailbox_quota_numeric}M" if mailbox_quota_numeric and mailbox_quota_numeric != "0" else "0"

    try:
        current = _wappos_api_user_detail(token, username)

        desired_aliases = {a.strip() for a in request.form.getlist("mail_aliases") if a.strip()}
        current_aliases = set(current["mail_aliases"])
        add_mailalias = list(desired_aliases - current_aliases)
        remove_mailalias = list(current_aliases - desired_aliases)

        desired_forwards = {f.strip() for f in request.form.getlist("mail_forward") if f.strip()}
        current_forwards = set(current["mail_forward"])
        add_mailforward = list(desired_forwards - current_forwards)
        remove_mailforward = list(current_forwards - desired_forwards)

        mail_changed = bool(mail and mail != current["mail"])

        if mail_changed and mail in remove_mailalias:
            remove_mailalias = [a for a in remove_mailalias if a != mail]

        mail_fields = {}
        if fullname and fullname != current["fullname"]:
            mail_fields["fullname"] = fullname
        if mail_changed:
            mail_fields["mail"] = mail
        if mailbox_quota != current["mailbox_quota_limit"]:
            mail_fields["mailbox_quota"] = mailbox_quota
        if change_password:
            mail_fields["change_password"] = change_password

        alias_fields = {}
        if add_mailalias:
            alias_fields["add_mailalias"] = add_mailalias
        if remove_mailalias:
            alias_fields["remove_mailalias"] = remove_mailalias
        if add_mailforward:
            alias_fields["add_mailforward"] = add_mailforward
        if remove_mailforward:
            alias_fields["remove_mailforward"] = remove_mailforward

        if not mail_fields and not alias_fields:
            return redirect(url_for("edit_user", username=username, error="Vous n'avez rien modifié."))

        if mail_fields:
            _wappos_api_update_user(token, username, **mail_fields)
        if alias_fields:
            _wappos_api_update_user(token, username, **alias_fields)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Update user detail %r failed: %s", username, e)
        return redirect(url_for("edit_user", username=username, error=_error_message(e)))
    except requests.exceptions.RequestException as e:
        app.logger.error("Update user detail %r failed: %s", username, e)
        return redirect(url_for("edit_user", username=username, error="L'API Wappos est injoignable."))

    return redirect(url_for("edit_user", username=username, msg=f"Compte {username} mis à jour."))


_YUNOHOST_WORD_RE = re.compile(r"\byunohost\b", re.IGNORECASE)


def _wappos_rebrand(text: str | None) -> str | None:
    if not text:
        return text

    def _repl(m: "re.Match[str]") -> str:
        s = m.group(0)
        if s == "YunoHost":
            return "Wappos"
        if s.isupper():
            return "WAPPOS"
        if s[:1].isupper():
            return "Wappos"
        return "wappos"

    return _YUNOHOST_WORD_RE.sub(_repl, text)


def _rebrand_diagnosis_text(reports: list[dict]) -> None:
    for report in reports:
        for item in report.get("items", []):
            if item.get("summary"):
                item["summary"] = _wappos_rebrand(item["summary"])
            details = item.get("details")
            if details:
                item["details"] = [_wappos_rebrand(d) for d in details]


def _rebrand_config_panels(panels: list[dict]) -> None:
    for panel in panels or []:
        if panel.get("help"):
            panel["help"] = _wappos_rebrand(panel["help"])
        for section in panel.get("sections", []):
            if section.get("help"):
                section["help"] = _wappos_rebrand(section["help"])
            if section.get("name"):
                section["name"] = _wappos_rebrand(section["name"])
            for option in section.get("options", []):
                if option.get("ask"):
                    option["ask"] = _wappos_rebrand(option["ask"])
                if option.get("help"):
                    option["help"] = _wappos_rebrand(option["help"])


def _rebrand_app_detail_text(detail: dict) -> None:
    if detail.get("description"):
        detail["description"] = _wappos_rebrand(detail["description"])
    if detail.get("notification_post_install"):
        detail["notification_post_install"] = _wappos_rebrand(detail["notification_post_install"])
    notifications_post_upgrade = detail.get("notifications_post_upgrade")
    if notifications_post_upgrade:
        detail["notifications_post_upgrade"] = {
            k: _wappos_rebrand(v) for k, v in notifications_post_upgrade.items()
        }
    upgrade = detail.get("upgrade")
    if upgrade:
        if upgrade.get("message"):
            upgrade["message"] = _wappos_rebrand(upgrade["message"])
        if upgrade.get("specific_channel_message"):
            upgrade["specific_channel_message"] = _wappos_rebrand(upgrade["specific_channel_message"])
        pre_upgrade_notifications = upgrade.get("pre_upgrade_notifications")
        if pre_upgrade_notifications:
            upgrade["pre_upgrade_notifications"] = {
                k: _wappos_rebrand(v) for k, v in pre_upgrade_notifications.items()
            }


def _strip_yunohost_doc_references(reports: list[dict]) -> None:
    for report in reports:
        for item in report.get("items", []):
            details = item.get("details")
            if details:
                item["details"] = [d for d in details if "doc.yunohost.org" not in d]


@app.route("/diagnosis")
def diagnosis():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        reports = _wappos_api_admin_diagnosis(token)
        categories = _wappos_api_diagnosis_categories(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load diagnosis for %r: %s", user, e)
        return render_template(
            "diagnosis.html", user=user, reports=[], categories=[], message=None,
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    _strip_yunohost_doc_references(reports)
    _rebrand_diagnosis_text(reports)

    already_run = {r["id"] for r in reports}
    never_run_categories = sorted(c for c in categories if c not in already_run)

    return render_template(
        "diagnosis.html", user=user, reports=reports, never_run_categories=never_run_categories,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/diagnosis/share", methods=["POST"])
def share_diagnosis():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        url = _wappos_api_diagnosis_share(token)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Share diagnosis failed: %s", e)
        return redirect(url_for("diagnosis", error=_error_message(e)))
    except requests.exceptions.RequestException as e:
        app.logger.error("Share diagnosis failed: %s", e)
        return redirect(url_for("diagnosis", error="L'API Wappos est injoignable."))

    return redirect(url_for("diagnosis", msg=f"Rapport partagé : {url}"))


@app.route("/diagnosis/run", methods=["POST"])
def run_diagnosis():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    category = request.form.get("category") or None

    try:
        _wappos_api_admin_run_diagnosis(token, category=category)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Run diagnosis (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error=_error_message(e)))
    except requests.exceptions.RequestException as e:
        app.logger.error("Run diagnosis (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error="L'API Wappos est injoignable."))

    return redirect(url_for("diagnosis", msg="Diagnostic relancé."))


@app.route("/diagnosis/<category>/ignore", methods=["POST"])
def ignore_diagnosis_item(category: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    meta = json.loads(request.form.get("meta", "{}"))

    try:
        _wappos_api_diagnosis_set_ignored(token, category, meta, ignored=True)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Ignore diagnosis item (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error=_error_message(e)))
    except requests.exceptions.RequestException as e:
        app.logger.error("Ignore diagnosis item (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error="L'API Wappos est injoignable."))

    return redirect(url_for("diagnosis", msg="Problème ignoré."))


@app.route("/diagnosis/<category>/unignore", methods=["POST"])
def unignore_diagnosis_item(category: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    meta = json.loads(request.form.get("meta", "{}"))

    try:
        _wappos_api_diagnosis_set_ignored(token, category, meta, ignored=False)
        reports = _wappos_api_admin_diagnosis(token)
        report = next((r for r in reports if r["id"] == category), None)
        still_ignored = report is not None and any(
            i.get("ignored") and i.get("meta", {}) == meta for i in report.get("items", [])
        )
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Unignore diagnosis item (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error=_error_message(e)))
    except requests.exceptions.RequestException as e:
        app.logger.error("Unignore diagnosis item (category=%r) failed: %s", category, e)
        return redirect(url_for("diagnosis", error="L'API Wappos est injoignable."))

    if still_ignored:
        return redirect(url_for("diagnosis", error="Aucun filtre correspondant trouvé — rien n'a été retiré."))
    return redirect(url_for("diagnosis", msg="Problème réintégré au rapport."))


_CRITICAL_SERVICES = {"nginx", "ssh", "slapd", "yunohost-api"}


@app.route("/services")
def services():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        service_list = _wappos_api_services(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load services for %r: %s", user, e)
        return render_template(
            "services.html", user=user, services=[], error="L'API Wappos est injoignable.",
            app_version=APP_VERSION,
        ), 503

    return render_template(
        "services.html", user=user, services=service_list,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/failed-units")
def failed_units_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    units = _failed_system_units_detail()
    return render_template("failed_units.html", user=user, units=units, app_version=APP_VERSION)


@app.route("/standalone-services")
def standalone_services_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    services = _standalone_services_status()
    return render_template("standalone_services.html", user=user, services=services, app_version=APP_VERSION)


def _redirect_to_service(name: str, *, message: str | None = None, error: str | None = None):
    target = url_for("service_info", name=name)
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


@app.route("/services/<name>")
def service_info(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        log_lines = int(request.args.get("lines", "50"))
    except ValueError:
        log_lines = 50
    log_lines = max(10, min(log_lines, 1000))

    try:
        info = _wappos_api_service_detail(token, name)
        logs = _wappos_api_service_log(token, name, number=log_lines)
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code in (400, 404):
            return redirect(url_for("services", error="Service inconnu."))
        app.logger.error("Failed to load service %r: %s", name, e)
        return redirect(url_for("services", error="L'API Wappos est injoignable."))
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load service %r: %s", name, e)
        return redirect(url_for("services", error="L'API Wappos est injoignable."))

    log_sources = sorted(logs.items(), key=lambda kv: (kv[0] != "journalctl", kv[0]))

    return render_template(
        "service_info.html", user=user, info=info, logs=log_sources, log_lines=log_lines,
        is_critical=name in _CRITICAL_SERVICES,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/services/<name>/<action>", methods=["POST"])
def run_service_action(name: str, action: str):
    if action not in ("start", "stop", "restart", "enable", "disable"):
        abort(404, description=f"unknown service action {action!r} for {name!r}")

    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    if name in _CRITICAL_SERVICES and action in ("stop", "disable") and request.form.get("confirm") != "1":
        return _redirect_to_service(
            name, error=f"Confirmation requise : {name} est un service critique.",
        )

    try:
        _wappos_api_service_action(token, name, action)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Service action %r on %r failed: %s", action, name, e)
        return _redirect_to_service(name, error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Service action %r on %r failed: %s", action, name, e)
        return _redirect_to_service(name, error="L'API Wappos est injoignable.")

    _ACTION_MESSAGES = {
        "start": "démarré", "stop": "arrêté", "restart": "redémarré",
        "enable": "activé au démarrage", "disable": "désactivé au démarrage",
    }
    return _redirect_to_service(name, message=f"Service {name} {_ACTION_MESSAGES[action]}.")


_LOG_OPERATION_CATEGORIES = {
    "app_install": ("Application", "app"),
    "app_remove": ("Application", "app"),
    "app_change_url": ("Application", "app"),
    "app_makedefault": ("Application", "app"),
    "app_config_set": ("Application", "app"),
    "backup_create": ("Sauvegarde", "backup"),
    "diagnosis_run": ("Diagnostic", "diagnosis"),
    "diagnosis_ignore": ("Diagnostic", "diagnosis"),
    "diagnosis_unignore": ("Diagnostic", "diagnosis"),
    "service_start": ("Service", "service"),
    "service_stop": ("Service", "service"),
    "service_restart": ("Service", "service"),
    "service_enable": ("Service", "service"),
    "service_disable": ("Service", "service"),
    "domain_add": ("Domaine", "domain"),
    "domain_remove": ("Domaine", "domain"),
    "domain_main_domain": ("Domaine", "domain"),
    "domain_config_set": ("Domaine", "domain"),
    "domain_dns_push": ("Domaine", "domain"),
    "dyndns_subscribe": ("DynDNS", "domain"),
    "dyndns_unsubscribe": ("DynDNS", "domain"),
    "dyndns_set_recovery_password": ("DynDNS", "domain"),
    "dyndns_update": ("DynDNS", "domain"),
    "user_create": ("Utilisateur", "user"),
    "user_delete": ("Utilisateur", "user"),
    "user_update": ("Utilisateur", "user"),
    "user_import": ("Utilisateur", "user"),
    "user_group_create": ("Groupe", "user"),
    "user_group_delete": ("Groupe", "user"),
    "user_group_update": ("Groupe", "user"),
    "settings_set": ("Réglages", "settings"),
    "settings_reset": ("Réglages", "settings"),
    "settings_reset_all": ("Réglages", "settings"),
    "tools_postinstall": ("Système", "system"),
    "tools_update": ("Système", "system"),
    "tools_upgrade": ("Système", "system"),
    "tools_shutdown": ("Système", "system"),
    "tools_reboot": ("Système", "system"),
    "regen_conf": ("Configuration", "system"),
}


def _categorize_log_entry(entry: dict) -> dict:
    parts = (entry.get("name") or "").split("-", 3)
    operation = parts[2] if len(parts) >= 3 else ""
    category, kind = _LOG_OPERATION_CATEGORIES.get(operation, ("Autre", "other"))
    entry = dict(entry)
    entry["category"] = category
    entry["kind"] = kind
    parsed = _parse_yunohost_datetime(entry.get("started_at"))
    local = parsed.astimezone(_LOCAL_TZ) if parsed else None
    entry["time_label"] = local.strftime("%H:%M") if local else "?"
    entry["local_date"] = local.strftime("%Y-%m-%d") if local else None
    return entry


@app.route("/logs")
def logs():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        log_list = _wappos_api_logs(token, limit=100)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load logs for %r: %s", user, e)
        return render_template(
            "logs.html", user=user, days=[], error="L'API Wappos est injoignable.",
            app_version=APP_VERSION,
        ), 503

    entries = [_categorize_log_entry(e) for e in log_list]

    days: dict[str, list[dict]] = {}
    for entry in entries:
        day_key = entry.get("local_date") or "Date inconnue"
        days.setdefault(day_key, []).append(entry)

    ordered_days = [
        {"date": d, "label": _day_label_fr(d), "entries": days[d]}
        for d in sorted(days.keys(), reverse=True)
    ]

    return render_template(
        "logs.html", user=user, days=ordered_days,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/logs/<name>")
def log_detail(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    number = request.args.get("n", default=25, type=int)

    try:
        detail = _wappos_api_log_detail(token, name, number=number)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load log %r: %s", name, e)
        return redirect(url_for("logs", error="L'API Wappos est injoignable."))

    return render_template(
        "log_detail.html", user=user, detail=detail, number=number,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/app-map")
def app_map_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        app_map = _wappos_api_app_map(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load app map for %r: %s", user, e)
        return render_template(
            "app_map.html", user=user, app_map={},
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    return render_template(
        "app_map.html", user=user, app_map=app_map,
        error=request.args.get("error"), app_version=APP_VERSION,
    )


@app.route("/domains/urlavailable")
def domain_url_available_check():
    user, token = _login_or_401()
    if not user:
        return {"available": None}, 401
    domain = (request.args.get("domain") or "").strip()
    path = (request.args.get("path") or "").strip()
    if not domain or not path:
        return {"available": None}
    try:
        available = _wappos_api_domain_url_available(token, domain, path)
    except requests.exceptions.RequestException:
        return {"available": None}
    return {"available": available}


@app.route("/firewall")
def firewall():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        rules = _wappos_api_firewall(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load firewall rules for %r: %s", user, e)
        return render_template(
            "firewall.html", user=user, rules={"tcp": [], "udp": [], "upnp_enabled": False},
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    return render_template(
        "firewall.html", user=user, rules=rules,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


def _redirect_to_firewall(*, message: str | None = None, error: str | None = None):
    target = url_for("firewall")
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


@app.route("/storage")
def storage():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        disks = _wappos_api_storage_disks(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load disks for %r: %s", user, e)
        return render_template(
            "storage.html", user=user, disks=[], mounts=[], smart_reports={},
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    try:
        mounts = _wappos_api_storage_mounts(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load mounts for %r: %s", user, e)
        mounts = []

    smart_reports = {}
    for disk in disks:
        try:
            smart_reports[disk["name"]] = _wappos_api_disk_smart(token, disk["name"])
        except requests.exceptions.RequestException as e:
            app.logger.error("Failed to load SMART for disk %r: %s", disk.get("name"), e)

    return render_template(
        "storage.html", user=user, disks=disks, mounts=mounts,
        smart_reports=smart_reports, app_version=APP_VERSION,
    )


_prometheus_password_file = Path(__file__).parent / ".package" / "prometheus_password"
PROMETHEUS_URL = "http://127.0.0.1:9090"
PROMETHEUS_USER = "wappos_admin_ro"
PROMETHEUS_APPS = ("wappos_admin", "wappos_portal", "wappos_api")


def _prometheus_password() -> str | None:
    if _prometheus_password_file.exists():
        return _prometheus_password_file.read_text().strip()
    return None


def _prometheus_query(promql: str) -> list[dict]:
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql},
        auth=(PROMETHEUS_USER, _prometheus_password()), timeout=5,
    )
    response.raise_for_status()
    return response.json()["data"]["result"]


def _prometheus_query_range(promql: str, start: float, end: float, step: int) -> list[dict]:
    response = requests.get(
        f"{PROMETHEUS_URL}/api/v1/query_range",
        params={"query": promql, "start": start, "end": end, "step": step},
        auth=(PROMETHEUS_USER, _prometheus_password()), timeout=5,
    )
    response.raise_for_status()
    return response.json()["data"]["result"]


def _prometheus_scalar(promql: str) -> float | None:
    result = _prometheus_query(promql)
    if not result:
        return None
    value = float(result[0]["value"][1])
    return None if math.isnan(value) else value


def _prometheus_series(promql: str, start: float, end: float, step: int) -> list[float]:
    result = _prometheus_query_range(promql, start, end, step)
    if not result:
        return []
    return [float(v[1]) for v in result[0]["values"]]


def _sparkline_svg(values: list[float], width: int = 160, height: int = 36) -> str:
    clean = [v for v in values if v == v]
    if len(clean) < 2:
        return ""
    lo, hi = min(clean), max(clean)
    span = hi - lo or 1.0
    step_x = width / (len(clean) - 1)
    points = " ".join(
        f"{i * step_x:.1f},{height - ((v - lo) / span) * height:.1f}"
        for i, v in enumerate(clean)
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="{width}" height="{height}" '
        f'xmlns="http://www.w3.org/2000/svg"><polyline points="{points}" '
        f'fill="none" stroke="currentColor" stroke-width="1.5"/></svg>'
    )


def _app_performance(app_name: str, now: float) -> dict:
    window = "5m"
    req_rate_q = f"sum(rate({app_name}_requests_total[{window}]))"
    error_rate_q = (
        f'100 * sum(rate({app_name}_requests_total{{status=~"5.."}}[{window}])) '
        f"/ sum(rate({app_name}_requests_total[{window}]))"
    )
    p95_q = (
        f"1000 * histogram_quantile(0.95, sum(rate("
        f"{app_name}_request_duration_seconds_bucket[{window}])) by (le))"
    )
    mem_q = f"{app_name}_process_resident_memory_bytes"

    req_rate = _prometheus_scalar(req_rate_q) or 0.0
    error_rate = _prometheus_scalar(error_rate_q) or 0.0
    p95 = _prometheus_scalar(p95_q)
    mem_bytes = _prometheus_scalar(mem_q)

    start = now - 6 * 3600
    req_series = _prometheus_series(req_rate_q, start, now, 300)
    mem_series = _prometheus_series(mem_q, start, now, 300)

    return {
        "name": app_name,
        "req_rate": round(req_rate, 2),
        "error_rate": round(error_rate, 1),
        "p95_ms": round(p95, 1) if p95 is not None else None,
        "mem_mb": round(mem_bytes / 1024 / 1024, 1) if mem_bytes is not None else None,
        "req_sparkline": _sparkline_svg(req_series),
        "mem_sparkline": _sparkline_svg(mem_series),
    }


@app.route("/performance")
def performance_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    if not _prometheus_password():
        return render_template(
            "performance.html", user=user, apps=[], available=False, app_version=APP_VERSION,
        )

    now = time.time()
    apps = []
    with ThreadPoolExecutor(max_workers=len(PROMETHEUS_APPS)) as executor:
        futures = {app_name: executor.submit(_app_performance, app_name, now) for app_name in PROMETHEUS_APPS}
        for app_name, future in futures.items():
            try:
                apps.append(future.result())
            except requests.exceptions.RequestException as e:
                app.logger.error("Failed to load Prometheus metrics for %r: %s", app_name, e)

    return render_template(
        "performance.html", user=user, apps=apps, available=bool(apps), app_version=APP_VERSION,
    )


@app.route("/settings")
def settings_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        data = _wappos_api_settings(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load settings for %r: %s", user, e)
        return render_template(
            "settings.html", user=user, panels=[],
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    _rebrand_config_panels(data.get("panels", []))

    return render_template(
        "settings.html", user=user, panels=data.get("panels", []),
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/settings/<panel_key>", methods=["POST"])
def settings_submit(panel_key: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    section_id = request.form.get("__section_id__")
    try:
        data = _wappos_api_settings(token)
        options = [
            o
            for panel in data.get("panels", [])
            if panel.get("id") == panel_key
            for section in panel.get("sections", [])
            if section.get("id") == section_id
            for o in section.get("options", [])
        ]
        args = _build_args_from_options(options, request.form, request.files)
        _wappos_api_set_settings(token, panel_key, args)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("settings_page", error=_error_message(e)))
    return redirect(url_for("settings_page", msg="Réglages appliqués."))


@app.route("/settings/reset-all", methods=["POST"])
def settings_reset_all():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_reset_all_settings(token)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("settings_page", error=_error_message(e)))
    return redirect(url_for("settings_page", msg="Tous les réglages ont été réinitialisés à leurs valeurs par défaut."))


@app.route("/settings/<key>/reset", methods=["POST"])
def setting_reset(key: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_reset_setting(token, key)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("settings_page", error=_error_message(e)))
    return redirect(url_for("settings_page", msg=f"Réglage « {key} » réinitialisé à sa valeur par défaut."))


@app.route("/domains")
def domains_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        domains = _wappos_api_domains(token, full=True)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load domains for %r: %s", user, e)
        return render_template(
            "domains.html", user=user, domains=[],
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    return render_template(
        "domains.html", user=user, domains=domains,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/domains/add", methods=["POST"])
def domain_add():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    domain = (request.form.get("domain") or "").strip()
    install_letsencrypt_cert = request.form.get("install_letsencrypt_cert") == "1"
    dyndns_recovery_password = request.form.get("dyndns_recovery_password") or None
    skip_dyndns_tos = request.form.get("skip_dyndns_tos") == "1"
    try:
        _wappos_api_add_domain(
            token,
            domain,
            install_letsencrypt_cert=install_letsencrypt_cert,
            dyndns_recovery_password=dyndns_recovery_password,
            skip_dyndns_tos=skip_dyndns_tos,
        )
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("domains_page", error=_error_message(e)))
    if install_letsencrypt_cert:
        try:
            refreshed = _wappos_api_domain_detail(token, domain)
        except requests.exceptions.RequestException:
            refreshed = {}
        ca_type = (refreshed.get("certificate") or {}).get("CA_type")
        if ca_type and ca_type != "letsencrypt":
            return redirect(url_for(
                "domain_detail", domain=domain,
                error="Domaine ajouté, mais le certificat Let's Encrypt n'a pas pu être installé "
                "(DNS pas encore propagé ?) — un certificat auto-signé est utilisé en attendant.",
            ))
    return redirect(url_for("domain_detail", domain=domain, msg="Domaine ajouté."))


_REGISTRAR_SUPPORTED_MARKER = "YunoHost a détecté automatiquement que ce domaine est géré par le registrar"


def _rewrite_registrar_supported_text(panels: list[dict], registrar: str | None) -> None:
    if not registrar:
        return
    new_text = (
        f"Ce domaine semble être géré par le registrar **{registrar}**. "
        "Si vous le souhaitez, vous pouvez utiliser la configuration automatique de cette zone DNS, "
        "si vous lui fournissez les identifiants API appropriés. "
        "Vous pouvez également configurer manuellement vos enregistrements DNS"
    )
    for panel in panels:
        for section in panel.get("sections", []):
            for o in section.get("options", []):
                ask = o.get("ask")
                if isinstance(ask, str) and _REGISTRAR_SUPPORTED_MARKER in ask:
                    o["ask"] = new_text


@app.route("/domains/<domain>")
def domain_detail(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        detail = _wappos_api_domain_detail(token, domain)
        config = _wappos_api_domain_config(token, domain)
        dns_suggestion = _wappos_api_domain_dns_suggest(token, domain)
        settings_data = _wappos_api_settings(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load domain detail for %r/%r: %s", user, domain, e)
        return render_template(
            "domain_detail.html", user=user, detail=None, panels=[], dns_suggestion="",
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    _rewrite_registrar_supported_text(config.get("panels", []), detail.get("registrar"))
    _rebrand_config_panels(config.get("panels", []))

    relay_options = {
        o.get("id"): o.get("value")
        for panel in settings_data.get("panels", [])
        if panel.get("id") == "email"
        for section in panel.get("sections", [])
        for o in section.get("options", [])
    }
    dns_suggestion, dns_adjusted_for_relay = _augment_dns_suggestion_for_smtp_relay(
        dns_suggestion, relay_options.get("smtp_relay_host")
    ) if relay_options.get("smtp_relay_enabled") else (dns_suggestion, False)

    dns_push_preview = None
    dns_push_error = None
    dns_push_checked = request.args.get("check_dns_push") == "1"
    if dns_push_checked:
        try:
            dns_push_preview = _wappos_api_push_domain_dns(token, domain, dry_run=True)
        except requests.exceptions.HTTPError as e:
            dns_push_error = _error_message(e)

    return render_template(
        "domain_detail.html", user=user, detail=detail, panels=config.get("panels", []),
        dns_suggestion=dns_suggestion, dns_adjusted_for_relay=dns_adjusted_for_relay,
        dns_push_preview=dns_push_preview, dns_push_error=dns_push_error, dns_push_checked=dns_push_checked,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


def _redirect_to_domain_detail(domain: str, *, message: str | None = None, error: str | None = None):
    target = url_for("domain_detail", domain=domain)
    if message:
        target += f"?msg={quote(message)}"
    elif error:
        target += f"?error={quote(error)}"
    return redirect(target)


@app.route("/domains/<domain>/config/<panel_key>", methods=["POST"])
def domain_config_submit(domain: str, panel_key: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    section_id = request.form.get("__section_id__")
    try:
        config = _wappos_api_domain_config(token, domain)
        options = [
            o
            for panel in config.get("panels", [])
            if panel.get("id") == panel_key
            for section in panel.get("sections", [])
            if section.get("id") == section_id
            for o in section.get("options", [])
        ]
        args = _build_args_from_options(options, request.form, request.files)
        _wappos_api_set_domain_config(token, domain, panel_key, args)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return _redirect_to_domain_detail(domain, message="Configuration appliquée.")


@app.route("/domains/<domain>/actions/<action_id>", methods=["POST"])
def domain_action_submit(domain: str, action_id: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        config = _wappos_api_domain_config(token, domain)
        panel_id, section_id, _button_id = action_id.split(".", 2)
        options = [
            o
            for panel in config.get("panels", [])
            if panel.get("id") == panel_id
            for section in panel.get("sections", [])
            if section.get("id") == section_id
            for o in section.get("options", [])
        ]
        args = _build_args_from_options(options, request.form, request.files)
        _wappos_api_run_domain_action(token, domain, action_id, args)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return _redirect_to_domain_detail(domain, message="Action exécutée.")


@app.route("/domains/<domain>/main", methods=["POST"])
def domain_set_main(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_set_main_domain(token, domain)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return _redirect_to_domain_detail(domain, message="Domaine principal changé.")


@app.route("/domains/<domain>/cert/install", methods=["POST"])
def domain_cert_install(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    force = request.form.get("force") == "1"
    self_signed = request.form.get("self_signed") == "1"
    no_checks = request.form.get("no_checks") == "1"
    try:
        _wappos_api_install_domain_certificate(
            token, domain, force=force, self_signed=self_signed, no_checks=no_checks
        )
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return _redirect_to_domain_detail(domain, message="Certificat installé.")


@app.route("/domains/<domain>/cert/renew", methods=["POST"])
def domain_cert_renew(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    force = request.form.get("force") == "1"
    email = request.form.get("email") == "1"
    no_checks = request.form.get("no_checks") == "1"
    try:
        _wappos_api_renew_domain_certificate(token, domain, force=force, email=email, no_checks=no_checks)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return _redirect_to_domain_detail(domain, message="Certificat renouvelé.")


@app.route("/domains/<domain>/remove", methods=["POST"])
def domain_remove(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    remove_apps = request.form.get("remove_apps") == "1"
    ignore_dyndns = request.form.get("ignore_dyndns") == "1"
    try:
        _wappos_api_remove_domain(token, domain, remove_apps=remove_apps, ignore_dyndns=ignore_dyndns)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    return redirect(url_for("domains_page", msg=f"Domaine {domain} supprimé."))


@app.route("/domains/<domain>/dns/push", methods=["POST"])
def domain_dns_push_submit(domain: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    force = request.form.get("force") == "1"
    try:
        result = _wappos_api_push_domain_dns(token, domain, dry_run=False, force=force)
    except requests.exceptions.HTTPError as e:
        return _redirect_to_domain_detail(domain, error=_error_message(e))
    errors = result.get("errors") or []
    warnings = result.get("warnings") or []
    if errors:
        return _redirect_to_domain_detail(
            domain, error=f"Le registrar a rejeté {len(errors)} enregistrement(s) DNS : " + "; ".join(errors)
        )
    if warnings:
        return _redirect_to_domain_detail(
            domain,
            message=f"Configuration DNS poussée, avec {len(warnings)} avertissement(s) : " + "; ".join(warnings),
        )
    return _redirect_to_domain_detail(domain, message="Configuration DNS poussée chez le registrar.")


_BACKUP_STATUS_LABELS = {
    "COMPLETE": ("Complète", "ok"),
    "INCOMPLETE": ("Incomplète", "warning"),
    "ERROR": ("Échec", "critical"),
}


def _backup_status(name: str, history_by_name: dict) -> dict:
    entry = history_by_name.get(name)
    if entry is None:
        return {"label": "Non suivie (créée avant l'activation du suivi)", "kind": "unknown", "failed_targets": []}
    label, kind = _BACKUP_STATUS_LABELS.get(entry.get("status"), ("Inconnu", "unknown"))
    failed = entry.get("failed_targets") or []
    if failed:
        label += f" — {len(failed)} cible(s) en échec"
    return {"label": label, "kind": kind, "failed_targets": failed}


@app.route("/backups")
def backups_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        result = _wappos_api_list_backups(token)
        installed_apps = _wappos_api_admin_apps(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load backups for %r: %s", user, e)
        return render_template(
            "backups.html", user=user, archives=[], installed_apps=[], schedule=backup_scheduler._DEFAULT_SCHEDULE,
            error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    history_by_name = {h.get("name"): h for h in backup_scheduler._load_history() if h.get("name")}
    archives = [
        (name, info, _backup_status(name, history_by_name))
        for name, info in reversed(list(result.get("archives", {}).items()))
    ]

    return render_template(
        "backups.html", user=user, archives=archives, installed_apps=installed_apps,
        schedule=backup_scheduler._load_schedule(),
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/backups/create", methods=["POST"])
def create_backup():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    name = request.form.get("name", "").strip() or None
    if name and not re.match(r"^[A-Za-z0-9_-]+$", name):
        return redirect(url_for("backups_page", error="Nom d'archive invalide (lettres, chiffres, - et _ uniquement)."))
    description = request.form.get("description", "").strip() or None
    apps = request.form.getlist("apps") or None
    try:
        result = _wappos_api_create_backup(token, name, description, None, apps)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("backups_page", error=_error_message(e)))
    archive_name = result.get("name", name or "")
    return redirect(url_for("backups_page", msg=f"Sauvegarde {archive_name} créée."))


@app.route("/backups/<name>")
def backup_detail(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        info = _wappos_api_backup_info(token, name)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load backup detail for %r/%r: %s", user, name, e)
        return redirect(url_for("backups_page", error="L'API Wappos est injoignable."))

    return render_template(
        "backup_detail.html", user=user, name=name, info=info,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/backups/<name>/download")
def download_backup(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    upstream = requests.get(
        f"{WAPPOS_API_BASE}/admin/backups/{name}/download",
        headers={"X-Admin-Token": token},
        timeout=320,
        stream=True,
    )
    try:
        upstream.raise_for_status()
    except requests.exceptions.HTTPError as e:
        upstream.close()
        return redirect(url_for("backup_detail", name=name, error=_error_message(e)))

    content_disposition = upstream.headers.get("content-disposition") or f'attachment; filename="{name}.tar.gz"'
    return Response(
        stream_with_context(upstream.iter_content(chunk_size=65536)),
        mimetype=upstream.headers.get("content-type", "application/octet-stream"),
        headers={"Content-Disposition": content_disposition},
    )


@app.route("/backups/<name>/restore", methods=["POST"])
def restore_backup(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    force = True

    try:
        info = _wappos_api_backup_info(token, name)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load backup info for restore %r: %s", name, e)
        return redirect(url_for("backup_detail", name=name, error="L'API Wappos est injoignable."))

    archive_apps = list((info.get("apps") or {}).keys())
    archive_system = list((info.get("system") or {}).keys())
    selected_apps = request.form.getlist("apps") or None if archive_apps else None
    selected_system = request.form.getlist("system") or None if archive_system else None

    if (archive_apps or archive_system) and selected_apps is None and selected_system is None:
        return redirect(url_for("backup_detail", name=name, error="Sélectionnez au moins un élément à restaurer."))

    try:
        _wappos_api_restore_backup(token, name, selected_system, selected_apps, force)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("backup_detail", name=name, error=_error_message(e)))
    return redirect(url_for("backup_detail", name=name, msg="Restauration terminée."))


@app.route("/backups/<name>/delete", methods=["POST"])
def delete_backup(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_delete_backup(token, name)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("backup_detail", name=name, error=_error_message(e)))
    return redirect(url_for("backups_page", msg=f"Archive {name} supprimée."))


@app.route("/backups/schedule", methods=["POST"])
def save_backup_schedule():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    schedule = backup_scheduler._load_schedule()
    schedule["enabled"] = request.form.get("enabled") == "1"
    schedule["frequency"] = "weekly" if request.form.get("frequency") == "weekly" else "daily"
    scope = request.form.get("scope")
    schedule["scope"] = "apps" if scope == "apps" else "full"
    schedule["apps"] = request.form.getlist("apps") if schedule["scope"] == "apps" else []

    schedule["retention_enabled"] = request.form.get("retention_enabled") == "1"
    schedule["retention_mode"] = "days" if request.form.get("retention_mode") == "days" else "count"
    try:
        schedule["retention_keep_count"] = max(1, int(request.form.get("retention_keep_count", 5)))
    except ValueError:
        schedule["retention_keep_count"] = 5
    try:
        schedule["retention_keep_days"] = max(1, int(request.form.get("retention_keep_days", 30)))
    except ValueError:
        schedule["retention_keep_days"] = 30

    backup_scheduler._save_schedule(schedule)
    return redirect(url_for("backups_page", msg="Réglages de sauvegarde automatique enregistrés."))


@app.route("/backups/retention/preview")
def preview_backup_retention():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    schedule = backup_scheduler._load_schedule()
    try:
        result = _wappos_api_list_backups(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load backups for retention preview: %s", e)
        return redirect(url_for("backups_page", error="L'API Wappos est injoignable."))

    archives = list(result.get("archives", {}).keys())
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

    if not to_delete:
        return redirect(url_for("backups_page", msg="Aperçu : aucune archive ne serait supprimée avec la politique actuelle."))
    return redirect(url_for(
        "backups_page",
        msg=f"Aperçu : {len(to_delete)} archive(s) seraient supprimées avec la politique actuelle — " + ", ".join(to_delete),
    ))


def _system_page_context(token: str) -> dict:
    versions = _wappos_api_versions(token)
    updates = _wappos_api_available_updates(token)
    installed_apps = _wappos_api_admin_apps(token)
    try:
        wappos_apps = sorted(_wappos_api_component_versions(token), key=lambda a: a["id"])
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load wappos component versions: %s", e)
        wappos_apps = _dedupe_by(
            sorted(
                (a for a in installed_apps if _is_wappos_infra_app(a.get("id", ""))),
                key=lambda a: a["id"],
            ),
            key=lambda a: (a.get("name"), a.get("version")),
        )
    if "apps" in updates:
        updates["apps"] = _dedupe_by(
            [a for a in updates["apps"] if not _is_wappos_infra_app(a.get("id", ""))],
            key=lambda a: (
                a.get("name"),
                (a.get("upgrade") or {}).get("current_version"),
                (a.get("upgrade") or {}).get("new_version"),
            ),
        )
    app_updates_confirmed = [a for a in updates.get("apps", []) if (a.get("upgrade") or {}).get("new_version")]
    app_updates_unknown = [a for a in updates.get("apps", []) if not (a.get("upgrade") or {}).get("new_version")]
    try:
        health = _wappos_api_system_health(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load system health: %s", e)
        health = None
    return {
        "versions": versions, "updates": updates, "wappos_apps": wappos_apps,
        "app_updates_confirmed": app_updates_confirmed, "app_updates_unknown": app_updates_unknown,
        "health": health,
    }


@app.route("/system")
def system_page():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        ctx = _system_page_context(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load system info for %r: %s", user, e)
        return render_template(
            "system.html", user=user, versions={}, updates={}, wappos_apps=[],
            app_updates_confirmed=[], app_updates_unknown=[], api_restart=False, regen_result=None,
            health=None, error="L'API Wappos est injoignable.", app_version=APP_VERSION,
        ), 503

    return render_template(
        "system.html", user=user, **ctx,
        api_restart=request.args.get("api_restart") == "1", regen_result=None,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/system/update/refresh", methods=["POST"])
def refresh_system_updates():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        _wappos_api_refresh_updates(token, target="all")
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))
    return redirect(url_for("system_page", msg="Liste des mises à jour rafraîchie."))


@app.route("/system/upgrade", methods=["POST"])
def run_system_upgrade():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    target = request.form.get("target", "")
    if target not in ("apps", "system"):
        return redirect(url_for("system_page", error="Cible de mise à jour invalide."))

    yunohost_being_upgraded = False
    if target == "system":
        try:
            pre_updates = _wappos_api_available_updates(token)
            yunohost_being_upgraded = any(
                p.get("name") == "yunohost"
                for packages in pre_updates.get("system", {}).values()
                for p in packages
            )
        except requests.exceptions.RequestException:
            pass

    if target == "apps":
        try:
            updates = _wappos_api_available_updates(token)
        except requests.exceptions.RequestException as e:
            return redirect(url_for("system_page", error=_error_message(e)))
        upgradable = [
            a for a in updates.get("apps", [])
            if not _is_wappos_infra_app(a.get("id", "")) and (a.get("upgrade") or {}).get("status") == "upgradable"
        ]
        if not upgradable:
            return redirect(url_for("system_page", msg="Aucune app au statut « à jour disponible » à mettre à jour."))
        done = 0
        for a in upgradable:
            try:
                _wappos_api_upgrade_app(token, a["id"], force=False)
                done += 1
            except requests.exceptions.HTTPError as e:
                return redirect(url_for(
                    "system_page",
                    error=f"{done} app(s) mise(s) à jour avant l'échec sur « {a.get('name') or a['id']} » : {_error_message(e)}",
                ))
        return redirect(url_for("system_page", msg=f"{done} app(s) mise(s) à jour."))

    try:
        _wappos_api_run_upgrade(token, target)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))

    if yunohost_being_upgraded:
        return redirect(url_for(
            "system_page",
            msg="Mise à jour système terminée — l'API Wappos redémarre, la page va se rafraîchir automatiquement.",
            api_restart="1",
        ))
    return redirect(url_for("system_page", msg=f"Mise à jour ({target}) terminée."))


@app.route("/system/regenconf", methods=["POST"])
def run_regen_conf():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    dry_run = request.form.get("dry_run") == "1"
    force = request.form.get("force") == "1"
    try:
        result = _wappos_api_regen_conf(token, dry_run=dry_run, force=force)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))

    applied_count = sum(len((cat or {}).get("applied", {})) for cat in (result or {}).values())
    pending_count = sum(len((cat or {}).get("pending", {})) for cat in (result or {}).values())
    verb = "Aperçu" if dry_run else "Régénération"

    try:
        ctx = _system_page_context(token)
    except requests.exceptions.RequestException:
        return redirect(url_for(
            "system_page",
            msg=f"{verb} de la configuration effectuée ({applied_count} appliquée(s), {pending_count} en attente).",
        ))

    return render_template(
        "system.html", user=user, **ctx,
        api_restart=False, regen_result=result,
        message=f"{verb} de la configuration effectuée ({applied_count} appliquée(s), {pending_count} en attente).",
        error=None, app_version=APP_VERSION,
    )


@app.route("/system/rootpw", methods=["POST"])
def change_root_password():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    new_password = request.form.get("new_password", "")
    new_password_confirm = request.form.get("new_password_confirm", "")
    if not new_password or new_password != new_password_confirm:
        return redirect(url_for("system_page", error="Les mots de passe ne correspondent pas."))
    try:
        _wappos_api_change_root_password(token, new_password)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))
    return redirect(url_for("system_page", msg="Mot de passe root changé."))


@app.route("/system/reboot", methods=["POST"])
def reboot_system():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    if request.form.get("confirm_word", "") != "REDEMARRER":
        return redirect(url_for("system_page", error="Pour redémarrer le serveur, tape exactement REDEMARRER dans le champ prévu."))
    try:
        _wappos_api_reboot(token)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))
    return redirect(url_for("system_page", msg="Redémarrage du serveur en cours."))


@app.route("/system/shutdown", methods=["POST"])
def shutdown_system():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    if request.form.get("confirm_word", "") != "ETEINDRE":
        return redirect(url_for("system_page", error="Pour éteindre le serveur, tape exactement ETEINDRE dans le champ prévu."))
    try:
        _wappos_api_shutdown(token)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("system_page", error=_error_message(e)))
    return redirect(url_for("system_page", msg="Extinction du serveur en cours."))


_PORT_OR_RANGE_RE = re.compile(r"^(\d{1,5})(?:-(\d{1,5}))?$")


@app.route("/firewall/apply", methods=["POST"])
def apply_firewall_operation():
    action = request.form.get("action", "open")
    protocol = request.form.get("protocol", "tcp")
    port = request.form.get("port", "").strip()
    if not port:
        return _redirect_to_firewall(error="Le port ne peut pas être vide.")

    match = _PORT_OR_RANGE_RE.match(port)
    if not match:
        return _redirect_to_firewall(error="Port invalide (attendu : un nombre ou une plage N-M).")
    bounds = [int(g) for g in match.groups() if g is not None]
    if any(b < 1 or b > 65535 for b in bounds):
        return _redirect_to_firewall(error="Le port doit être compris entre 1 et 65535 (0 n'est pas autorisé).")
    if len(bounds) == 2 and bounds[0] >= bounds[1]:
        return _redirect_to_firewall(error="Plage de ports invalide (le premier port doit être inférieur au second).")

    if action == "close":
        return close_firewall_port(protocol, port)
    return open_firewall_port(protocol, port)


@app.route("/firewall/<protocol>/<port>/open", methods=["POST"])
def open_firewall_port(protocol: str, port: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    comment = request.form.get("comment", "").strip()
    upnp = request.form.get("upnp") == "on"

    try:
        _wappos_api_open_firewall_port(token, protocol, port, comment=comment, upnp=upnp)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Open firewall port %s/%s failed: %s", protocol, port, e)
        return _redirect_to_firewall(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Open firewall port %s/%s failed: %s", protocol, port, e)
        return _redirect_to_firewall(error="L'API Wappos est injoignable.")

    return _redirect_to_firewall(message=f"Port {port}/{protocol} ouvert.")


@app.route("/firewall/<protocol>/<port>/close", methods=["POST"])
def close_firewall_port(protocol: str, port: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    upnp_only = request.form.get("upnp_only") == "on"

    try:
        _wappos_api_close_firewall_port(token, protocol, port, upnp_only=upnp_only)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Close firewall port %s/%s failed: %s", protocol, port, e)
        return _redirect_to_firewall(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Close firewall port %s/%s failed: %s", protocol, port, e)
        return _redirect_to_firewall(error="L'API Wappos est injoignable.")

    return _redirect_to_firewall(message=f"Port {port}/{protocol} fermé.")


@app.route("/firewall/upnp/<enabled>", methods=["POST"])
def set_upnp(enabled: str):
    if enabled not in ("true", "false"):
        abort(404, description=f"unknown upnp value {enabled!r}")

    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        _wappos_api_set_upnp(token, enabled == "true")
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Set UPnP (%s) failed: %s", enabled, e)
        return _redirect_to_firewall(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Set UPnP (%s) failed: %s", enabled, e)
        return _redirect_to_firewall(error="L'API Wappos est injoignable.")

    return _redirect_to_firewall(message=f"UPnP {'activé' if enabled == 'true' else 'désactivé'}.")


@app.route("/users", methods=["POST"])
def create_user():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    username = request.form.get("username", "").strip()
    domain = request.form.get("domain", "").strip()
    fullname = request.form.get("fullname", "").strip()
    new_password = request.form.get("new_password", "")
    new_password_confirm = request.form.get("new_password_confirm", "")

    if not username or not domain or not fullname or not new_password:
        return _redirect_with_message(error="Tous les champs sont obligatoires pour créer un utilisateur.")
    if new_password != new_password_confirm:
        return _redirect_with_message(error="Les mots de passe ne correspondent pas.")

    try:
        _wappos_api_create_user(
            token, username=username, domain=domain, password=new_password, fullname=fullname,
        )
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Create user %r failed: %s", username, e)
        return _redirect_with_message(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Create user %r failed: %s", username, e)
        return _redirect_with_message(error="L'API Wappos est injoignable.")

    return _redirect_with_message(message=f"Utilisateur {username} créé.")


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    purge = request.form.get("purge") == "1"
    try:
        _wappos_api_delete_user(token, username, purge=purge)
    except requests.exceptions.HTTPError as e:
        app.logger.warning("Delete user %r failed: %s", username, e)
        return _redirect_with_message(error=_error_message(e))
    except requests.exceptions.RequestException as e:
        app.logger.error("Delete user %r failed: %s", username, e)
        return _redirect_with_message(error="L'API Wappos est injoignable.")

    return _redirect_with_message(message=f"Utilisateur {username} supprimé.")


@app.route("/docker")
def docker_apps():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    real_ids = None
    try:
        real_ids = {a["id"] for a in _wappos_api_admin_apps(token)}
    except requests.exceptions.RequestException as e:
        app.logger.warning("Failed to fetch YunoHost app list for docker reconciliation: %s", e)

    docker_apps_list = docker_gate.list_apps(real_ids)

    return render_template(
        "docker_apps.html", user=user, apps=docker_apps_list,
        docker_installed=docker_gate.docker_available(),
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


_DOCKER_VISIBILITY_FR = {
    "admins": "Administrateurs uniquement",
    "all_users": "Tous les comptes",
    "visitors": "Visiteurs (public)",
}


@app.route("/docker/add", methods=["GET", "POST"])
def docker_add():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    if request.method == "GET":
        try:
            domains = _wappos_api_domains(token, full=True)
        except requests.exceptions.RequestException as e:
            app.logger.error("Failed to load domains for docker add form: %s", e)
            domains = []
        current_domain = request.host.split(":")[0]
        catalogue = docker_gate.fetch_app_catalogue()
        return render_template(
            "docker_add.html", user=user, domains=domains, current_domain=current_domain,
            catalogue_apps=catalogue["apps"], catalogue_source=catalogue["source"],
            app_version=APP_VERSION,
        )

    slug = request.form.get("slug", "").strip().lower()
    image = request.form.get("image", "").strip()
    container_port = request.form.get("container_port", "").strip()
    mode = request.form.get("mode", "path")
    domain = request.form.get("domain", "").strip()
    domain_parent = request.form.get("domain_parent", "").strip()
    path = request.form.get("path", "").strip()
    new_subdomain = request.form.get("new_subdomain", "").strip().lower()
    visibility = request.form.get("visibility", "admins").strip()
    if visibility not in ("admins", "all_users", "visitors"):
        visibility = "admins"
    data_path = request.form.get("data_path", "").strip()
    env_vars_text = request.form.get("env_vars", "").strip()
    url_env_var = request.form.get("url_env_var", "").strip()
    cpu_limit = request.form.get("cpu_limit", "").strip()
    mem_limit = request.form.get("mem_limit", "").strip()
    ldap_enabled = request.form.get("ldap_enabled") == "on"
    catalogue_logo_url = request.form.get("catalogue_logo_url", "").strip()
    reuse_existing_domain = request.form.get("reuse_existing_domain") == "on"

    companions_json = request.form.get("companions_json", "").strip()
    main_service_key = request.form.get("main_service_key", "").strip() or None
    companions = []

    config_files_json = request.form.get("config_files_json", "").strip()
    config_files = []

    try:
        env_vars = docker_gate.parse_env_vars_text(env_vars_text) if env_vars_text else {}
        if companions_json:
            for c in json.loads(companions_json):
                companions.append({
                    "service_key": c.get("service_key"),
                    "image": c.get("image"),
                    "data_path": (c.get("data_path") or "").strip() or None,
                    "env_vars": docker_gate.parse_env_vars_text(c["env_vars"]) if c.get("env_vars") else {},
                })
        if config_files_json:
            for cf in json.loads(config_files_json):
                config_files.append({
                    "container_path": cf.get("container_path"),
                    "filename": cf.get("filename"),
                    "content": cf.get("content") or "",
                })
    except (docker_gate.DockerGateError, ValueError) as e:
        try:
            domains = _wappos_api_domains(token, full=True)
        except requests.exceptions.RequestException:
            domains = []
        return render_template("docker_add.html", user=user, domains=domains, error=str(e), form=request.form, app_version=APP_VERSION)

    confirmed = request.form.get("confirmed") == "1"
    if not confirmed:
        try:
            target_url = docker_gate.resolve_target_url(mode, domain, domain_parent, path, new_subdomain)
        except docker_gate.DockerGateError as e:
            try:
                domains = _wappos_api_domains(token, full=True)
            except requests.exceptions.RequestException:
                domains = []
            return render_template("docker_add.html", user=user, domains=domains, error=str(e), form=request.form, app_version=APP_VERSION)
        preview = {
            "slug": slug, "image": image, "container_port": container_port,
            "target_url": target_url, "visibility_fr": _DOCKER_VISIBILITY_FR.get(visibility, visibility),
            "has_volume": bool(data_path), "data_path": data_path,
            "env_vars_count": len(env_vars), "companions": companions, "config_files": config_files,
            "cpu_limit": cpu_limit, "mem_limit": mem_limit, "ldap_enabled": ldap_enabled,
            "ldap_env_preview": docker_gate.ldap_env_vars() if ldap_enabled else {},
            "has_catalogue_logo": bool(catalogue_logo_url),
        }
        return render_template(
            "docker_confirm.html", user=user, preview=preview,
            form_fields=list(request.form.items()), app_version=APP_VERSION,
        )

    steps = docker_gate.build_create_steps(mode)
    job_id = docker_progress.create_job(steps)

    def _add_domain(d):
        _wappos_api_add_domain(token, d)

    def _run_diag(category):
        try:
            _wappos_api_admin_run_diagnosis(token, category)
            return True
        except requests.exceptions.RequestException:
            return False

    def _install_cert(d):
        _wappos_api_install_domain_certificate(token, d)

    def _domain_detail(d):
        return _wappos_api_domain_detail(token, d)

    def _install_app(app_id, label, args):
        _wappos_api_install_app(token, app_id, label, args)

    def _list_app_ids():
        return {a["id"] for a in _wappos_api_admin_apps(token)}

    def _set_permission_logo(permission, filename, content):
        _wappos_api_update_permission_logo(token, permission, filename, content)

    def run_creation():
        try:
            logo_bytes = docker_gate.fetch_catalogue_logo_bytes(catalogue_logo_url) if catalogue_logo_url else None
            entry = docker_gate.create_docker_app(
                slug=slug, image=image, container_port=container_port, mode=mode,
                domain=domain, domain_parent=domain_parent, path=path, new_subdomain=new_subdomain,
                visibility=visibility, data_path=data_path, env_vars=env_vars, url_env_var=url_env_var,
                reuse_existing_domain=reuse_existing_domain,
                companions=companions, main_service_key=main_service_key, config_files=config_files,
                cpu_limit=cpu_limit, mem_limit=mem_limit, ldap_enabled=ldap_enabled, logo_bytes=logo_bytes,
                on_step=lambda label: docker_progress.advance(job_id, label),
                add_domain_fn=_add_domain, run_diagnosis_fn=_run_diag, install_cert_fn=_install_cert,
                domain_detail_fn=_domain_detail, install_app_fn=_install_app, list_app_ids_fn=_list_app_ids,
                set_permission_logo_fn=_set_permission_logo,
            )
            docker_progress.finish(job_id, warnings=entry.get("warnings", []))
        except docker_gate.DockerGateError as e:
            docker_progress.fail(job_id, str(e))
        except Exception as e:
            docker_progress.fail(job_id, f"Erreur inattendue : {e}")

    threading.Thread(target=run_creation, daemon=True).start()
    return redirect(url_for("docker_progress_page", job_id=job_id, slug=slug))


@app.route("/docker/check_subdomain")
def docker_check_subdomain():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    new_subdomain = request.args.get("new_subdomain", "").strip().lower()
    domain_parent = request.args.get("domain_parent", "").strip()
    if not new_subdomain or not domain_parent:
        return {"status": "invalid"}
    result = docker_gate.check_subdomain_status(
        new_subdomain, domain_parent,
        existing_domains_fn=lambda: _wappos_api_domains(token, full=True),
        domain_detail_fn=lambda d: _wappos_api_domain_detail(token, d),
    )
    return result


@app.route("/docker/check_path")
def docker_check_path():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    domain = request.args.get("domain", "").strip()
    path = request.args.get("path", "").strip()
    if not domain or not path:
        return {"status": "invalid"}
    result = docker_gate.check_path_status(
        domain, path, list_apps_fn=lambda: _wappos_api_admin_apps(token),
    )
    return result


@app.route("/docker/parse_input", methods=["POST"])
def docker_parse_input():
    user, token = _login_or_401()
    if not user:
        return {"ok": False, "error": "Unauthorized"}, 401
    payload = request.get_json(silent=True) or {}
    url = payload.get("url", "").strip()

    env_example_text = None
    if url:
        try:
            raw_text = docker_gate.fetch_compose_from_url(url)
        except docker_gate.DockerGateError as e:
            return {"ok": False, "error": str(e)}
        try:
            env_example_text = docker_gate.fetch_env_example_from_url(url)
        except Exception:
            env_example_text = None
    else:
        raw_text = payload.get("text", "")

    try:
        result = docker_gate.smart_parse_input(raw_text, env_example_text=env_example_text)
        if url:
            result["raw_text"] = raw_text
        return {"ok": True, **result}
    except docker_gate.DockerGateError as e:
        return {"ok": False, "error": str(e)}


@app.route("/docker/progress/<job_id>")
def docker_progress_page(job_id):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    job = docker_progress.get_job(job_id)
    if job is None:
        return redirect(url_for("docker_apps", error="Suivi de progression introuvable (le service a peut-être redémarré)."))
    slug = request.args.get("slug", "")
    action_label = request.args.get("action_label", "Installation")
    return render_template(
        "docker_progress.html", user=user, job_id=job_id, steps=job["steps"], slug=slug,
        action_label=action_label, app_version=APP_VERSION,
    )


@app.route("/docker/progress/<job_id>/status")
def docker_progress_status(job_id):
    user, token = _login_or_401()
    if not user:
        return {"error": "unauthorized"}, 401
    job = docker_progress.get_job(job_id)
    if job is None:
        return {"error": "not_found"}, 404
    return job


@app.route("/docker/remove/<slug>", methods=["POST"])
def docker_remove(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    delete_data = request.form.get("delete_data") == "on"
    delete_domain = request.form.get("delete_domain") == "on"

    def _remove_app(app_id):
        _wappos_api_remove_app(token, app_id, purge=False)

    def _remove_domain(d):
        _wappos_api_remove_domain(token, d)

    try:
        warnings = docker_gate.remove_docker_app(
            slug, delete_data=delete_data, delete_domain=delete_domain,
            remove_app_fn=_remove_app, remove_domain_fn=_remove_domain,
        )
        msg = f"App {slug} supprimée."
        for w in warnings:
            app.logger.warning("Docker app removal warning (%s): %s", slug, w)
        return redirect(url_for("docker_apps", msg=msg))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_apps", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_apps", error=f"Erreur inattendue : {e}"))


@app.route("/docker/action/<slug>/<action>", methods=["POST"])
def docker_action(slug: str, action: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    if action not in ("start", "stop", "restart"):
        return "Action inconnue", 400

    _ACTION_LABELS = {"start": "démarrée", "stop": "arrêtée", "restart": "redémarrée"}
    try:
        docker_gate.container_action(slug, action)
        return redirect(url_for("docker_apps", msg=f"App {slug} {_ACTION_LABELS[action]}."))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_apps", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_apps", error=f"Erreur inattendue : {e}"))


@app.route("/docker/check_update/<slug>")
def docker_check_update(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        result = docker_gate.check_docker_app_update(slug)
    except docker_gate.DockerGateError as e:
        return {"checked": False, "error": str(e)}, 200
    return result, 200


@app.route("/docker/update/<slug>", methods=["GET", "POST"])
def docker_update(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        entry = docker_gate.get_app_entry(slug)
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_apps", error=str(e)))

    if request.method == "GET":
        tags, tags_error = [], None
        try:
            tags = docker_gate.list_available_image_tags(entry["image"])
        except docker_gate.DockerGateError as e:
            tags_error = str(e)
        return render_template(
            "docker_update.html", user=user, slug=slug, entry=entry, tags=tags, tags_error=tags_error,
            error=request.args.get("error"), app_version=APP_VERSION,
        )

    target_tag = request.form.get("target_tag", "").strip() or None

    steps = ["Vérification des paramètres", "Écriture de la configuration", "Récupération de la nouvelle image", "Redémarrage du conteneur"]
    job_id = docker_progress.create_job(steps)

    def run_update():
        try:
            docker_gate.apply_docker_app_update(
                slug, target_tag=target_tag,
                on_step=lambda label: docker_progress.advance(job_id, label),
            )
            docker_progress.finish(job_id, warnings=[])
        except docker_gate.DockerGateError as e:
            docker_progress.fail(job_id, str(e))
        except Exception as e:
            docker_progress.fail(job_id, f"Erreur inattendue : {e}")

    threading.Thread(target=run_update, daemon=True).start()
    return redirect(url_for("docker_progress_page", job_id=job_id, slug=slug, action_label="Mise à jour"))


@app.route("/docker/edit/<slug>", methods=["GET", "POST"])
def docker_edit(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        entry = docker_gate.get_app_entry(slug)
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_apps", error=str(e)))

    if request.method == "GET":
        current_env_vars = docker_gate.read_current_env_vars(slug)
        env_vars_text = "\n".join(f"{k}={v}" for k, v in sorted(current_env_vars.items()))
        app_permissions, groups = {}, []
        supports_change_url, domains = False, []
        yunohost_app_id = entry.get("yunohost_app_id")
        if yunohost_app_id:
            try:
                all_permissions = _wappos_api_admin_permissions(token)
                app_permissions = {
                    pid: p for pid, p in all_permissions.items() if pid.startswith(f"{yunohost_app_id}.")
                }
                groups = _wappos_api_admin_groups(token)
            except (requests.exceptions.RequestException, SessionExpiredError):
                pass
            try:
                detail = _wappos_api_app_detail(token, yunohost_app_id)
                supports_change_url = bool(detail.get("supports_change_url"))
                domains = _wappos_api_domains(token)
            except (requests.exceptions.RequestException, SessionExpiredError):
                pass
        return render_template(
            "docker_edit.html", user=user, slug=slug, entry=entry, env_vars_text=env_vars_text,
            app_permissions=app_permissions, groups=groups,
            supports_change_url=supports_change_url, domains=domains,
            error=request.args.get("error"), message=request.args.get("msg"),
            app_version=APP_VERSION,
        )

    image = request.form.get("image", "").strip()
    container_port = request.form.get("container_port", "").strip()
    data_path = request.form.get("data_path", "").strip()
    env_vars_text = request.form.get("env_vars", "").strip()
    cpu_limit = request.form.get("cpu_limit", "").strip()
    mem_limit = request.form.get("mem_limit", "").strip()
    ldap_enabled = request.form.get("ldap_enabled") == "on"

    try:
        env_vars = docker_gate.parse_env_vars_text(env_vars_text) if env_vars_text else {}
    except docker_gate.DockerGateError as e:
        return render_template(
            "docker_edit.html", user=user, slug=slug, entry=entry, env_vars_text=env_vars_text,
            error=str(e), app_version=APP_VERSION,
        )

    steps = docker_gate.build_edit_steps()
    job_id = docker_progress.create_job(steps)

    def run_update():
        try:
            updated = docker_gate.update_docker_app(
                slug, image=image, container_port=container_port, data_path=data_path,
                env_vars=env_vars, cpu_limit=cpu_limit, mem_limit=mem_limit, ldap_enabled=ldap_enabled,
                on_step=lambda label: docker_progress.advance(job_id, label),
            )
            docker_progress.finish(job_id, warnings=updated.get("warnings", []))
        except docker_gate.DockerGateError as e:
            docker_progress.fail(job_id, str(e))
        except Exception as e:
            docker_progress.fail(job_id, f"Erreur inattendue : {e}")

    threading.Thread(target=run_update, daemon=True).start()
    return redirect(url_for("docker_progress_page", job_id=job_id, slug=slug, action_label="Édition"))


@app.route("/docker/change_url/<slug>", methods=["POST"])
def docker_change_url(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    try:
        entry = docker_gate.get_app_entry(slug)
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_apps", error=str(e)))

    yunohost_app_id = entry.get("yunohost_app_id")
    if not yunohost_app_id:
        return redirect(url_for("docker_edit", slug=slug, error="Aucune app YunoHost associée."))

    domain = request.form.get("domain", "").strip()
    raw_path = request.form.get("path", "").strip()
    if not domain or not raw_path:
        return redirect(url_for("docker_edit", slug=slug, error="Domaine et chemin requis."))
    path = "/" + raw_path.lstrip("/")

    try:
        _wappos_api_change_app_url(token, yunohost_app_id, domain, path)
    except requests.exceptions.HTTPError as e:
        return redirect(url_for("docker_edit", slug=slug, error=_error_message(e)))
    except requests.exceptions.RequestException:
        return redirect(url_for("docker_edit", slug=slug, error="L'API Wappos est injoignable."))

    docker_gate.update_docker_app_url(slug, domain, path)
    return redirect(url_for("docker_edit", slug=slug, msg="URL modifiée."))


@app.route("/docker/logs/<slug>")
def docker_logs(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    tail = request.args.get("tail", type=int, default=200)
    try:
        logs = docker_gate.get_container_logs(slug, tail=tail)
        error = None
    except docker_gate.DockerGateError as e:
        logs = ""
        error = str(e)
    return render_template(
        "docker_logs.html", user=user, slug=slug, logs=logs, tail=tail,
        error=error, app_version=APP_VERSION,
    )


@app.route("/docker/stats/<slug>")
def docker_stats(slug: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        stats = docker_gate.get_container_stats(slug)
        return jsonify({"ok": True, **stats})
    except docker_gate.DockerGateError as e:
        return jsonify({"ok": False, "error": str(e)}), 404


@app.route("/docker/audit")
def docker_audit():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401

    warnings = []

    def _safe(fn, *args, default=None, label=""):
        try:
            return fn(*args)
        except docker_gate.DockerGateError as e:
            warnings.append(f"{label} : {e}")
            return default if default is not None else []
        except Exception as e:
            warnings.append(f"{label} : erreur inattendue ({e})")
            return default if default is not None else []

    orphan_containers = _safe(docker_gate.find_orphan_containers, label="Conteneurs orphelins")
    orphan_volumes = _safe(docker_gate.find_orphan_volumes, label="Volumes orphelins")
    orphan_networks = _safe(docker_gate.find_orphan_networks, label="Réseaux orphelins")
    dangling_images = _safe(docker_gate.find_dangling_images, label="Images inutilisées")
    try:
        empty_domains = docker_gate.find_empty_domains(
            existing_domains_fn=lambda: _wappos_api_domains(token, full=True),
            domain_detail_fn=lambda d: _wappos_api_domain_detail(token, d),
        )
    except Exception as e:
        warnings.append(f"Domaines vides : {e}")
        empty_domains = []
    ce_status = _safe(docker_gate.docker_ce_status, default={"installed": False, "tracked_containers": [], "foreign_containers": []}, label="État de Docker CE")

    return render_template(
        "docker_audit.html", user=user,
        orphan_containers=orphan_containers, orphan_volumes=orphan_volumes,
        orphan_networks=orphan_networks, dangling_images=dangling_images,
        empty_domains=empty_domains, ce_status=ce_status, warnings=warnings,
        error=request.args.get("error"), message=request.args.get("msg"),
        app_version=APP_VERSION,
    )


@app.route("/docker/audit/remove_container/<name>", methods=["POST"])
def docker_audit_remove_container(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        docker_gate.remove_orphan_container(name)
        return redirect(url_for("docker_audit", msg=f"Conteneur {name} supprimé."))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_audit", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_audit", error=f"Erreur inattendue : {e}"))


@app.route("/docker/audit/remove_volume/<name>", methods=["POST"])
def docker_audit_remove_volume(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        docker_gate.remove_orphan_volume(name)
        return redirect(url_for("docker_audit", msg=f"Volume {name} supprimé."))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_audit", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_audit", error=f"Erreur inattendue : {e}"))


@app.route("/docker/audit/remove_network/<name>", methods=["POST"])
def docker_audit_remove_network(name: str):
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        docker_gate.remove_orphan_network(name)
        return redirect(url_for("docker_audit", msg=f"Réseau {name} supprimé."))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_audit", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_audit", error=f"Erreur inattendue : {e}"))


@app.route("/docker/audit/prune_images", methods=["POST"])
def docker_audit_prune_images():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        freed = docker_gate.prune_dangling_images()
        freed_mb = round(freed / (1024 * 1024), 1)
        return redirect(url_for("docker_audit", msg=f"Images nettoyées, {freed_mb} Mo libérés."))
    except docker_gate.DockerGateError as e:
        return redirect(url_for("docker_audit", error=str(e)))
    except Exception as e:
        return redirect(url_for("docker_audit", error=f"Erreur inattendue : {e}"))


@app.route("/docker/audit/uninstall_docker_ce", methods=["POST"])
def docker_audit_uninstall_docker_ce():
    user, token = _login_or_401()
    if not user:
        return "Unauthorized", 401
    try:
        warnings = docker_gate.uninstall_docker_ce()
        for w in warnings:
            app.logger.warning("Docker CE uninstall warning: %s", w)
        msg = "Docker CE désinstallé." if not warnings else "Docker CE désinstallé, avec avertissements (voir journaux)."
        return redirect(url_for("docker_audit", msg=msg))
    except Exception as e:
        return redirect(url_for("docker_audit", error=f"Erreur inattendue : {e}"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9500)
