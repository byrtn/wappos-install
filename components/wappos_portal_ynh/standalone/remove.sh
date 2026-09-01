#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl stop "$app" 2>/dev/null || true
systemctl disable "$app" 2>/dev/null || true
systemctl stop "$app.socket" 2>/dev/null || true
systemctl disable "$app.socket" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service" "/etc/systemd/system/$app.socket"
systemctl daemon-reload

for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
    rm -f "/etc/nginx/conf.d/${existing_domain}.d/${app}_crossdomain.conf"
done
nginx -t && systemctl reload nginx

rm -f "/etc/yunohost/hooks.d/post_domain_add/50-$app"
rm -f "/etc/yunohost/hooks.d/post_domain_remove/50-$app"
rm -f "/etc/cron.d/$app"
rm -rf "$install_dir"
userdel "$app" 2>/dev/null || true

echo "wappos_portal desinstalle (standalone)."
