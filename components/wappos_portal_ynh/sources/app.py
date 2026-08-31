# Auteur : Patrick Ritaine
import json
import os
import re
import secrets
import smtplib
import time
import tomllib
from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path

import requests
from flask import Flask, Response, abort, g, jsonify, make_response, redirect, render_template, request, session, url_for
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest, multiprocess
from werkzeug.middleware.proxy_fix import ProxyFix

import i18n

app = Flask(__name__)

app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1, x_prefix=1)

_secret_key_file = Path(__file__).parent / ".package" / "secret_key"
if not _secret_key_file.exists():
    _secret_key_file.parent.mkdir(parents=True, exist_ok=True)
    _secret_key_file.write_text(secrets.token_hex(32))
app.secret_key = _secret_key_file.read_text().strip()

app.config["SESSION_COOKIE_NAME"] = "wappos_portal_session"
app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=3)

WAPPOS_API_BASE = "http://127.0.0.1:9400"

LANG_COOKIE_NAME = "wappos_portal_lang"
LANG_COOKIE_MAX_AGE = 60 * 60 * 24 * 365

_MANIFEST = tomllib.loads((Path(__file__).parent / ".package" / "manifest.toml").read_text())
APP_VERSION = _MANIFEST["version"]

OWN_APP_FAMILY = _MANIFEST["id"]

_metrics_token_file = Path(__file__).parent / ".package" / "metrics_token"
if not _metrics_token_file.exists():
    _metrics_token_file.parent.mkdir(parents=True, exist_ok=True)
    _metrics_token_file.write_text(secrets.token_hex(32))
METRICS_TOKEN = _metrics_token_file.read_text().strip()

_REQUEST_COUNT = Counter(
    "wappos_portal_requests_total", "Nombre de requêtes HTTP traitées",
    ["method", "endpoint", "status"],
)
_REQUEST_LATENCY = Histogram(
    "wappos_portal_request_duration_seconds", "Durée des requêtes HTTP",
    ["method", "endpoint"],
)
_PROCESS_MEMORY = Gauge(
    "wappos_portal_process_resident_memory_bytes", "Mémoire résidente du worker",
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


def _same_app_family(perm_id: str, family: str) -> bool:
    app_id = perm_id.rsplit(".", 1)[0]
    return app_id.split("__")[0] == family


def _is_wappos_infra_app(perm_id: str) -> bool:
    app_id = perm_id.rsplit(".", 1)[0].split("__")[0]
    return app_id.startswith("wappos_")

TILE_ORDER_DIR = Path(__file__).parent / "data" / "tile_order"


def _current_user() -> str | None:
    return session.get("user")


def _safe_next_path(raw: str | None) -> str | None:
    if not raw or not raw.startswith("/") or raw.startswith("//"):
        return None
    if "\\" in raw or "\n" in raw or "\r" in raw:
        return None
    return raw


class SessionExpiredError(Exception):
    pass


def _raise_for_status(resp: "requests.Response") -> None:
    if resp.status_code == 401:
        raise SessionExpiredError()
    resp.raise_for_status()


@app.errorhandler(SessionExpiredError)
def _handle_session_expired(_exc):
    session.clear()
    lang = get_lang()
    return render_template(
        "login.html", user=None, app_version=APP_VERSION, year=date.today().year,
        hide_chrome=True, next=_safe_next_path(request.path),
        error=i18n.t("err_session_expired", lang),
        **_anonymous_context(),
    ), 401


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    next_path = _safe_next_path(request.form.get("next"))
    try:
        token, portal_cookie = _wappos_api_login(username, password)
    except requests.exceptions.HTTPError:
        lang = get_lang()
        return render_template(
            "login.html", user=None, app_version=APP_VERSION, year=date.today().year,
            hide_chrome=True, next=next_path,
            error_username=i18n.t("err_possibly_invalid_username", lang),
            error_password=i18n.t("err_possibly_invalid_password", lang),
            **_anonymous_context(),
        ), 401
    except requests.exceptions.RequestException:
        return render_template(
            "login.html", user=None, app_version=APP_VERSION, year=date.today().year,
            hide_chrome=True, next=next_path,
            error=i18n.t("err_server_unreachable", get_lang()),
            **_anonymous_context(),
        ), 503
    session.permanent = True
    session["user"] = username
    session["token"] = token
    g.portal_cookie = portal_cookie
    return redirect(next_path or url_for("index"))


@app.route("/logout", methods=["POST"])
def logout():
    token = session.get("token")
    if token:
        try:
            g.portal_cookie = _wappos_api_logout(token)
        except requests.exceptions.RequestException as e:
            app.logger.error("Portal logout relay failed: %s", e)
    session.clear()
    return redirect(url_for("index"))


def get_lang() -> str:
    return i18n.normalize_lang(request.cookies.get(LANG_COOKIE_NAME))


app.jinja_env.globals["t"] = lambda key, **kwargs: i18n.t(key, get_lang(), **kwargs)
app.jinja_env.globals["current_lang"] = get_lang


@app.route("/set_language/<lang>")
def set_language(lang):
    lang = i18n.normalize_lang(lang)
    target = request.referrer or url_for("index")
    resp = make_response(redirect(target))
    resp.set_cookie(LANG_COOKIE_NAME, lang, max_age=LANG_COOKIE_MAX_AGE)
    return resp


def _order_file(user: str) -> Path:
    safe_user = re.sub(r"[^a-zA-Z0-9_.-]", "_", user)
    return TILE_ORDER_DIR / f"{safe_user}.json"


def _load_order(user: str) -> list[str]:
    path = _order_file(user)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_order(user: str, order: list[str]) -> None:
    TILE_ORDER_DIR.mkdir(parents=True, exist_ok=True)
    _order_file(user).write_text(json.dumps(order))


def _wappos_api_host_header() -> dict[str, str]:
    return {"X-Portal-Host": request.host}


def _wappos_api_login(user: str, password: str) -> tuple[str, str | None]:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/portal/login",
        json={"user": user, "password": password},
        headers=_wappos_api_host_header(),
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["token"], data.get("cookie")


_PORTAL_COOKIE_NAME = "yunohost.portal"


@app.after_request
def _relay_portal_cookie(response):
    cookie_header = getattr(g, "portal_cookie", None)
    if cookie_header:
        host = request.host.split(":")[0]
        for domain in (None, host):
            response.set_cookie(
                _PORTAL_COOKIE_NAME, "", expires=0, path="/",
                domain=domain, secure=True, httponly=True, samesite="Lax",
            )
        response.headers.add("Set-Cookie", cookie_header)
    return response


def _wappos_api_logout(token: str) -> str | None:
    resp = requests.post(
        f"{WAPPOS_API_BASE}/portal/logout",
        headers={**_wappos_api_host_header(), "X-Portal-Token": token},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json().get("cookie")


def _wappos_api_me(token: str) -> dict:
    resp = requests.get(
        f"{WAPPOS_API_BASE}/portal/me",
        headers={**_wappos_api_host_header(), "X-Portal-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)
    return resp.json()


def _wappos_api_update(token: str, **fields) -> None:
    resp = requests.put(
        f"{WAPPOS_API_BASE}/portal/update",
        json=fields,
        headers={**_wappos_api_host_header(), "X-Portal-Token": token},
        timeout=10,
    )
    _raise_for_status(resp)


def _wappos_api_public(token: str | None = None) -> dict:
    headers = _wappos_api_host_header()
    if token:
        headers["X-Portal-Token"] = token
    resp = requests.get(f"{WAPPOS_API_BASE}/portal/public", headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def _header_info(me: dict) -> dict:
    role = "Administrateur" if "admins" in me.get("groups", []) else "Utilisateur"
    return {"mail": me["mail"], "role": role}


def _list_tiles(apps: dict, user: str | None) -> list[dict]:
    tiles = [
        {
            "id": perm_id,
            "label": infos["label"],
            "url": infos["url"],
            "logo": infos.get("logo"),
            "description": infos.get("description"),
        }
        for perm_id, infos in apps.items()
        if not _same_app_family(perm_id, OWN_APP_FAMILY) and not _is_wappos_infra_app(perm_id)
    ]

    if user:
        saved_order = _load_order(user)
        if saved_order:
            rank = {perm_id: i for i, perm_id in enumerate(saved_order)}
            tiles.sort(key=lambda t: rank.get(t["id"], len(saved_order)))

    return tiles


def _anonymous_context() -> dict:
    public = _public_settings_safe()
    tiles = _list_tiles(public.get("apps", {}), user=None) if public.get("public") else []
    return {
        "public_intro": public.get("portal_public_intro"),
        "tiles": tiles,
        "tile_theme": public.get("portal_tile_theme", "simple"),
    }


def _public_settings_safe(token: str | None = None) -> dict:
    try:
        return _wappos_api_public(token)
    except requests.exceptions.RequestException as e:
        app.logger.warning("Failed to fetch public portal settings: %s", e)
        return {}


_branding_cache: dict = {"value": None, "fetched_at": 0.0}
_BRANDING_CACHE_TTL = 5


@app.before_request
def _load_branding():
    if request.endpoint in ("reorder", "metrics"):
        return

    now = time.monotonic()
    if _branding_cache["value"] is None or now - _branding_cache["fetched_at"] > _BRANDING_CACHE_TTL:
        _branding_cache["value"] = _public_settings_safe()
        _branding_cache["fetched_at"] = now
    public = _branding_cache["value"]

    logo = public.get("portal_logo")
    g.branding = {
        "logo_url": f"/yunohost/sso/customassets/{logo}" if logo else None,
    }


@app.context_processor
def _inject_branding():
    return {"branding": getattr(g, "branding", {"logo_url": None})}


@app.route("/")
def index():
    user = _current_user()
    if not user:
        return render_template(
            "login.html", user=None, app_version=APP_VERSION, year=date.today().year,
            hide_chrome=True, next=_safe_next_path(request.args.get("next")),
            **_anonymous_context(),
        )

    try:
        token = session.get("token")
        me = _wappos_api_me(token)
        tiles = _list_tiles(me["apps"], user)
        header = _header_info(me)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to load portal data for %r: %s", user, e)
        return render_template(
            "index.html", user=user, tiles=[], header=None,
            error=i18n.t("err_api_unreachable", get_lang()),
            app_version=APP_VERSION, year=date.today().year,
        ), 503

    public = _public_settings_safe(token)
    return render_template(
        "index.html", user=user, tiles=tiles, header=header,
        user_intro=public.get("portal_user_intro"),
        search_engine=public.get("search_engine"),
        search_engine_name=public.get("search_engine_name"),
        tile_theme=public.get("portal_tile_theme", "simple"),
        app_version=APP_VERSION, year=date.today().year,
    )


@app.route("/reorder", methods=["POST"])
def reorder():
    user = _current_user()
    if not user:
        return jsonify(error="unauthenticated"), 401

    order = request.get_json(silent=True) or {}
    order = order.get("order")
    if not isinstance(order, list) or not all(isinstance(i, str) for i in order):
        return jsonify(error="invalid order"), 400

    _save_order(user, order)
    return jsonify(ok=True)


@app.route("/documentation")
def documentation():
    user = _current_user()
    if not user:
        return redirect(url_for("index", next=request.path))
    lang = get_lang()
    return render_template(
        "static_page.html", user=user, header=None,
        page_title=i18n.t("page_title_documentation", lang),
        page_body=i18n.t("page_body_documentation", lang),
        app_version=APP_VERSION, year=date.today().year,
    )


@app.route("/support")
def support():
    user = _current_user()
    if not user:
        return redirect(url_for("index", next=request.path))
    lang = get_lang()
    return render_template(
        "support.html", user=user, header=None,
        page_title=i18n.t("page_title_support", lang),
        faq_html=i18n.t("page_body_support_faq", lang),
        domain=request.host,
        message=request.args.get("sent") and i18n.t("msg_contact_sent", lang),
        error=None,
        app_version=APP_VERSION, year=date.today().year,
    )


@app.route("/support/contact", methods=["POST"])
def support_contact():
    user = _current_user()
    if not user:
        return redirect(url_for("index", next=request.path))
    lang = get_lang()

    name = request.form.get("name", "").strip()
    sender_email = request.form.get("email", "").strip()
    body = request.form.get("message", "").strip()
    rgpd = request.form.get("rgpd")

    if not name or not sender_email or not body or not rgpd:
        return render_template(
            "support.html", user=user, header=None,
            page_title=i18n.t("page_title_support", lang),
            faq_html=i18n.t("page_body_support_faq", lang),
            domain=request.host, message=None,
            error=i18n.t("err_contact_missing_fields", lang),
            app_version=APP_VERSION, year=date.today().year,
        )

    try:
        msg = EmailMessage()
        msg["From"] = f"wappos-portal-contact@{request.host}"
        msg["To"] = "contact@byrtn.fr"
        msg["Reply-To"] = sender_email
        msg["Subject"] = f"[wappos-portal] Contact de {name} ({request.host})"
        msg.set_content(
            f"De : {name} <{sender_email}>\nDomaine : {request.host}\nCompte : {user}\n\n{body}",
            charset="utf-8",
        )
        smtp = smtplib.SMTP("localhost")
        smtp.send_message(msg)
        smtp.quit()
    except OSError as e:
        app.logger.error("Failed to send contact message: %s", e)
        return render_template(
            "support.html", user=user, header=None,
            page_title=i18n.t("page_title_support", lang),
            faq_html=i18n.t("page_body_support_faq", lang),
            domain=request.host, message=None,
            error=i18n.t("err_contact_send_failed", lang),
            app_version=APP_VERSION, year=date.today().year,
        )

    return redirect(url_for("support", sent="1"))


@app.route("/profile", methods=["GET", "POST"])
def profile():
    user = _current_user()
    if not user:
        return redirect(url_for("index", next=request.path))
    token = session.get("token")

    message = None
    error = None
    lang = get_lang()

    try:
        public_settings = _wappos_api_public(token)
    except requests.exceptions.RequestException:
        public_settings = {}
    can_edit_email = bool(public_settings.get("portal_allow_edit_email", False))
    can_edit_email_alias = bool(public_settings.get("portal_allow_edit_email_alias", False))
    can_edit_email_forward = bool(public_settings.get("portal_allow_edit_email_forward", False))

    if request.method == "POST":
        action = request.form.get("action")
        try:
            if action == "update_info":
                fullname = request.form.get("fullname", "").strip()
                mailalias = [a.strip() for a in request.form.getlist("mailalias") if a.strip()]
                mailforward = [f.strip() for f in request.form.getlist("mailforward") if f.strip()]
                fields = {"mailalias": mailalias, "mailforward": mailforward}
                if fullname:
                    fields["fullname"] = fullname
                if can_edit_email:
                    mail = request.form.get("mail", "").strip()
                    if mail:
                        fields["mail"] = mail
                _wappos_api_update(token, **fields)
                message = i18n.t("msg_profile_updated", lang)

            elif action == "change_password":
                current_password = request.form.get("current_password", "")
                new_password = request.form.get("new_password", "")
                confirm_password = request.form.get("confirm_password", "")
                if not new_password or new_password != confirm_password:
                    error = i18n.t("err_password_mismatch", lang)
                else:
                    try:
                        _wappos_api_update(
                            token, currentpassword=current_password, newpassword=new_password
                        )
                    except requests.exceptions.HTTPError as e:
                        error_key = None
                        try:
                            error_key = e.response.json().get("detail", {}).get("code")
                        except (ValueError, AttributeError):
                            pass
                        if error_key == "invalid_password":
                            error = i18n.t("err_invalid_current_password", lang)
                        else:
                            raise
                    else:
                        token, portal_cookie = _wappos_api_login(user, new_password)
                        session["token"] = token
                        g.portal_cookie = portal_cookie
                        message = i18n.t("msg_password_updated", lang)
        except requests.exceptions.RequestException as e:
            app.logger.error("Profile action %r failed: %s", action, e)
            error = i18n.t("err_action_failed", lang)

    try:
        me = _wappos_api_me(token)
    except requests.exceptions.RequestException as e:
        app.logger.error("Failed to fetch profile info for %r: %s", user, e)
        return render_template(
            "index.html", user=user, tiles=[], header=None,
            error=i18n.t("err_api_unreachable", get_lang()),
            app_version=APP_VERSION, year=date.today().year,
        ), 503

    info = {
        "username": me["username"],
        "fullname": me["fullname"],
        "mail": me["mail"],
        "mail-aliases": me["mailalias"],
        "mail-forward": me["mailforward"],
    }

    return render_template(
        "profile.html", user=user, info=info, message=message, error=error,
        can_edit_email=can_edit_email, can_edit_email_alias=can_edit_email_alias,
        can_edit_email_forward=can_edit_email_forward,
        header=_header_info(me), app_version=APP_VERSION, year=date.today().year,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=9300)
