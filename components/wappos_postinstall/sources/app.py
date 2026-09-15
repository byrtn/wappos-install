# Auteur : Patrick Ritaine
import os
import re
import subprocess

from flask import Flask, jsonify, render_template, request

import i18n

app = Flask(__name__)

INSTALLED_MARKER = "/etc/yunohost/installed"
LANGUAGE_FILE = "/etc/wappos/language"
CONSOLE_LOG = "/var/log/wappos-install-console.log"
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")

SENTINEL_COMPLETE = "===WAPPOS_INSTALL_COMPLETE==="
SENTINEL_FAILED = "===WAPPOS_INSTALL_FAILED==="

_ANSI_CODE_RE = re.compile(r"\033\[([0-9;]*)m")


def already_installed() -> bool:
    return os.path.exists(INSTALLED_MARKER)


def get_lang() -> str:
    try:
        with open(LANGUAGE_FILE, encoding="utf-8") as f:
            return i18n.normalize_lang(f.read().strip())
    except OSError:
        return i18n.DEFAULT_LANG


_STEP_HEADER_RE = re.compile(r"^(?:Etape|Step)\s+(\d+)\b", re.MULTILINE)


def _parse_progress_steps(raw: str, lang: str) -> dict:
    plain = _ANSI_CODE_RE.sub("", raw)
    matches = _STEP_HEADER_RE.findall(plain)
    current = int(matches[-1]) if matches else 0
    done = SENTINEL_COMPLETE in raw
    failed = SENTINEL_FAILED in raw

    steps = []
    for idx, entry in enumerate(i18n.PROGRESS_STEPS, start=1):
        title = entry.get(lang) or entry.get(i18n.DEFAULT_LANG)
        if done:
            state = "done"
        elif idx < current:
            state = "done"
        elif idx == current:
            state = "failed" if failed else "current"
        else:
            state = "pending"
        steps.append({"title": title, "state": state})

    long_hint = None
    if not done and not failed and current in i18n.PROGRESS_LONG_STEP_INDEXES:
        long_hint = i18n.t("progress_long_step_hint", lang)

    return {"steps": steps, "current": current, "total": len(i18n.PROGRESS_STEPS), "long_hint": long_hint}


@app.route("/progress-log")
def progress_log():
    lang = get_lang()
    try:
        with open(CONSOLE_LOG, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError:
        raw = ""
    progress = _parse_progress_steps(raw, lang)
    step_label = None
    if progress["current"]:
        step_label = i18n.t("progress_step_label", lang, current=progress["current"], total=progress["total"])
    return jsonify(
        done=SENTINEL_COMPLETE in raw,
        failed=SENTINEL_FAILED in raw,
        steps=progress["steps"],
        step_label=step_label,
        long_hint=progress["long_hint"],
    )


@app.route("/", methods=["GET", "POST"])
def postinstall():
    lang = get_lang()
    app.jinja_env.globals["t"] = lambda key, **kwargs: i18n.t(key, lang, **kwargs)
    app.jinja_env.globals["lang"] = lang

    if already_installed():
        return render_template("progress.html", domain=None)

    error = None
    domain = request.form.get("domain", "").strip()
    username = request.form.get("username", "wappos_admin").strip()
    fullname = request.form.get("fullname", i18n.t("default_fullname", lang)).strip()

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not domain:
            error = i18n.t("err_domain_empty", lang)
        elif not USERNAME_RE.match(username):
            error = i18n.t("err_username_invalid", lang)
        elif not password or password != password_confirm:
            error = i18n.t("err_passwords_mismatch", lang)
        elif len(password) < 8:
            error = i18n.t("err_password_too_short", lang)
        elif password.lower() in (username.lower(), fullname.lower(), domain.lower()):
            error = i18n.t("err_password_too_similar", lang)
        else:
            result = subprocess.run(
                [
                    "sudo", "-n", "/usr/bin/yunohost", "tools", "postinstall",
                    "-d", domain,
                    "-u", username,
                    "-F", fullname,
                    "-p", password,
                    "--i-have-read-terms-of-services",
                ],
                capture_output=True,
                text=True,
                timeout=3600,
            )
            if result.returncode != 0:
                output_lines = (result.stderr + "\n" + result.stdout).strip().splitlines()
                error_lines = [
                    line for line in output_lines
                    if line.strip().lower().startswith("error") or "traceback" in line.lower()
                ]
                if error_lines:
                    error = error_lines[-1].strip()
                elif output_lines:
                    error = output_lines[-1].strip()
                else:
                    error = i18n.t("err_unknown_setup_failure", lang)
            else:
                return render_template("progress.html", domain=domain)

    return render_template(
        "postinstall.html",
        error=error,
        domain=domain,
        username=username,
        fullname=fullname,
    )
