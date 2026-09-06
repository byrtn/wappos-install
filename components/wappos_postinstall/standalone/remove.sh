#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl disable --now "$app.service" "$app.socket" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service" "/etc/systemd/system/$app.socket"
systemctl daemon-reload

rm -f /etc/sudoers.d/wappos_postinstall_yunohost
rm -f "/etc/yunohost/hooks.d/post_domain_add/50-$app"
rm -rf "$install_dir"

# Ne retire le fragment nginx que s'il pointe encore vers nous : si un domaine
# a deja ete cree, wappos_portal/wappos_sso_bypass l'ont deja remplace par leur
# propre redirection legitime, qu'il ne faut surtout pas casser.
redirect_conf="/etc/nginx/conf.d/default.d/redirect_to_admin.conf"
if [ -f "$redirect_conf" ] && grep -q "127.0.0.1:$port" "$redirect_conf"; then
    rm -f "$redirect_conf"
    nginx -t && systemctl reload nginx
fi

if id "$app" >/dev/null 2>&1; then
    userdel "$app"
fi

echo "wappos_postinstall retire."
