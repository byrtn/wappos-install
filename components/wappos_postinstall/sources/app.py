# Auteur : Patrick Ritaine
import os
import re
import subprocess

from flask import Flask, render_template, request

app = Flask(__name__)

INSTALLED_MARKER = "/etc/yunohost/installed"
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]+$")


def already_installed() -> bool:
    return os.path.exists(INSTALLED_MARKER)


@app.route("/", methods=["GET", "POST"])
def postinstall():
    if already_installed():
        return render_template("postinstall.html", done=True)

    error = None
    domain = request.form.get("domain", "").strip()
    username = request.form.get("username", "wappos_admin").strip()
    fullname = request.form.get("fullname", "Administrateur").strip()

    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not domain:
            error = "Le nom de domaine ne peut pas etre vide."
        elif not USERNAME_RE.match(username):
            error = "L'identifiant ne peut contenir que des lettres, chiffres et underscore."
        elif not password or password != password_confirm:
            error = "Les mots de passe ne correspondent pas ou sont vides."
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
                timeout=120,
            )
            if result.returncode != 0:
                output_lines = (result.stderr + "\n" + result.stdout).strip().splitlines()
                error_lines = [l for l in output_lines if l.strip().startswith("ERROR")]
                if error_lines:
                    error = error_lines[-1].strip()
                elif output_lines:
                    error = output_lines[-1].strip()
                else:
                    error = "Echec inconnu de la configuration."
            else:
                return render_template("postinstall.html", done=True, domain=domain)

    return render_template(
        "postinstall.html",
        done=False,
        error=error,
        domain=domain,
        username=username,
        fullname=fullname,
    )
