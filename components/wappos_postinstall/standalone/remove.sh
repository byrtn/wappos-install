#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl disable --now "$app.service" "$app.socket" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service" "/etc/systemd/system/$app.socket"
systemctl daemon-reload

rm -f /etc/sudoers.d/wappos_postinstall_yunohost
rm -f "/etc/yunohost/hooks.d/post_domain_add/50-$app"
rm -rf "$install_dir"

if id "$app" >/dev/null 2>&1; then
    userdel "$app"
fi

echo "wappos_postinstall retire."
