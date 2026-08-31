#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl stop "$app" 2>/dev/null || true
systemctl disable "$app" 2>/dev/null || true
rm -f "/etc/systemd/system/$app.service"
systemctl daemon-reload

rm -rf "$install_dir" "$config_dir" "$data_dir"
userdel "$app" 2>/dev/null || true

echo "prometheus desinstalle (standalone)."
