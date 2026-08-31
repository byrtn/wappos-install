#!/bin/bash
# Auteur : Patrick Ritaine


venv_dir="$install_dir/venv"

_compute_admin_alert_mail() {
	admin_alert_mail="$(yunohost user info adminynh --output-as json 2>/dev/null \
		| python3 -c 'import json,sys; print(json.load(sys.stdin).get("mail",""))' 2>/dev/null)"
	if [ -z "$admin_alert_mail" ]; then
		main_domain="$(yunohost domain list --output-as json 2>/dev/null \
			| python3 -c 'import json,sys; print(json.load(sys.stdin).get("main",""))' 2>/dev/null)"
		ynh_print_warn --message="Impossible de déterminer l'adresse mail réelle d'adminynh — repli sur adminynh@$main_domain, qui peut ne pas exister."
		admin_alert_mail="adminynh@$main_domain"
	fi
}
