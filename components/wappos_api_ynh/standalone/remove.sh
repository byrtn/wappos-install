#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl stop "$app" 2>/dev/null || true
systemctl disable "$app" 2>/dev/null || true
systemctl stop "$app.socket" 2>/dev/null || true
systemctl disable "$app.socket" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service" "/etc/systemd/system/$app.socket"
systemctl daemon-reload

rm -rf "$install_dir"
userdel "$app" 2>/dev/null || true

echo "wappos_api desinstalle (standalone)."
