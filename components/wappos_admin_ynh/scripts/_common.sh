#!/bin/bash
# Auteur : Patrick Ritaine


venv_dir="$install_dir/venv"


_compute_admin_alert_mail() {
	admin_username="$(yunohost user list --output-as json 2>/dev/null \
		| python3 -c 'import json,sys; print(next(iter(json.load(sys.stdin).get("users",{})), ""))' 2>/dev/null)" || admin_username=""
	admin_alert_mail="$(yunohost user info "$admin_username" --output-as json 2>/dev/null \
		| python3 -c 'import json,sys; print(json.load(sys.stdin).get("mail",""))' 2>/dev/null)" || admin_alert_mail=""
	if [ -z "$admin_alert_mail" ]; then
		main_domain="$(yunohost domain list --output-as json 2>/dev/null \
			| python3 -c 'import json,sys; print(json.load(sys.stdin).get("main",""))' 2>/dev/null)" || main_domain=""
		ynh_print_warn --message="Could not determine the admin's real mail address — falling back to ${admin_username:-adminynh}@$main_domain, which may not exist."
		admin_alert_mail="${admin_username:-adminynh}@$main_domain"
	fi
}
