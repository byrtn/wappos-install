# Auteur : Patrick Ritaine
import html
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
_CLEAR_EOL_RE = re.compile(r"\033\[K")
_ANSI_COLORS = {
    "31": "#e5534b",
    "32": "#3fb950",
    "33": "#d29922",
    "36": "#58a6ff",
}


def already_installed() -> bool:
    return os.path.exists(INSTALLED_MARKER)


def get_lang() -> str:
    try:
        with open(LANGUAGE_FILE, encoding="utf-8") as f:
            return i18n.normalize_lang(f.read().strip())
    except OSError:
        return i18n.DEFAULT_LANG


def _collapse_carriage_returns(raw: str) -> str:
    lines = []
    for line in raw.split("\n"):
        if "\r" in line:
            line = line.split("\r")[-1]
        lines.append(_CLEAR_EOL_RE.sub("", line))
    return "\n".join(lines)


def ansi_to_html(raw: str) -> str:
    text = _collapse_carriage_returns(raw)
    text = text.replace(SENTINEL_COMPLETE, "").replace(SENTINEL_FAILED, "")
    out = []
    pos = 0
    bold = False
    underline = False
    color = None
    open_span = False

    def close_span():
        nonlocal open_span
        if open_span:
            out.append("</span>")
            open_span = False

    def emit(chunk: str):
        nonlocal open_span
        if not chunk:
            return
        close_span()
        if bold or underline or color:
            styles = []
            if bold:
                styles.append("font-weight:700")
            if underline:
                styles.append("text-decoration:underline")
            if color:
                styles.append(f"color:{color}")
            out.append(f'<span style="{";".join(styles)}">')
            open_span = True
        out.append(html.escape(chunk))

    for m in _ANSI_CODE_RE.finditer(text):
        emit(text[pos:m.start()])
        codes = m.group(1).split(";") if m.group(1) else ["0"]
        for code in codes:
            if code in ("", "0"):
                bold = underline = False
                color = None
            elif code == "1":
                bold = True
            elif code == "4":
                underline = True
            elif code in _ANSI_COLORS:
                color = _ANSI_COLORS[code]
        pos = m.end()

    emit(text[pos:])
    close_span()
    return "".join(out)


@app.route("/progress-log")
def progress_log():
    try:
        with open(CONSOLE_LOG, encoding="utf-8", errors="replace") as f:
            raw = f.read()
    except OSError:
        raw = ""
    return jsonify(
        html=ansi_to_html(raw),
        done=SENTINEL_COMPLETE in raw,
        failed=SENTINEL_FAILED in raw,
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
