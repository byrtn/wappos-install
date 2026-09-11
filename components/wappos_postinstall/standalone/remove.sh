#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl disable --now "$app.service" "$app.socket" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service" "/etc/systemd/system/$app.socket"
systemctl daemon-reload

rm -f /etc/sudoers.d/wappos_postinstall_yunohost
rm -f "/etc/yunohost/hooks.d/post_domain_add/50-$app"
rm -rf "$install_dir"

redirect_conf="/etc/nginx/conf.d/default.d/redirect_to_admin.conf"
progress_conf="/etc/nginx/conf.d/default.d/wappos_postinstall_progress.conf"
removed_any=0
if [ -f "$redirect_conf" ] && grep -q "127.0.0.1:$port" "$redirect_conf"; then
    rm -f "$redirect_conf"
    removed_any=1
fi
if [ -f "$progress_conf" ]; then
    rm -f "$progress_conf"
    removed_any=1
fi
if [ "$removed_any" = 1 ]; then
    nginx -t && systemctl reload nginx
fi

if id "$app" >/dev/null 2>&1; then
    userdel "$app"
fi

echo "wappos_postinstall retire."
