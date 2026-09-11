# Auteur : Patrick Ritaine
import os
import re
import subprocess

from flask import Flask, render_template, request

import i18n

app = Flask(__name__)

INSTALLED_MARKER = "/etc/yunohost/installed"
LANGUAGE_FILE = "/etc/wappos/language"
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def already_installed() -> bool:
    return os.path.exists(INSTALLED_MARKER)


def get_lang() -> str:
    try:
        with open(LANGUAGE_FILE, encoding="utf-8") as f:
            return i18n.normalize_lang(f.read().strip())
    except OSError:
        return i18n.DEFAULT_LANG


@app.route("/", methods=["GET", "POST"])
def postinstall():
    lang = get_lang()
    app.jinja_env.globals["t"] = lambda key, **kwargs: i18n.t(key, lang, **kwargs)
    app.jinja_env.globals["lang"] = lang

    if already_installed():
        return render_template("postinstall.html", done=True)

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
                    l for l in output_lines
                    if l.strip().lower().startswith("error") or "traceback" in l.lower()
                ]
                if error_lines:
                    error = error_lines[-1].strip()
                elif output_lines:
                    error = output_lines[-1].strip()
                else:
                    error = i18n.t("err_unknown_setup_failure", lang)
            else:
                subprocess.run(
                    [
                        "sudo", "-n", "/usr/bin/systemd-run",
                        "--on-active=5s", "--unit=wappos_postinstall-selfdisable",
                        "/bin/systemctl", "disable", "--now",
                        "wappos_postinstall.service", "wappos_postinstall.socket",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                return render_template("postinstall.html", done=True, domain=domain)

    return render_template(
        "postinstall.html",
        done=False,
        error=error,
        domain=domain,
        username=username,
        fullname=fullname,
    )
