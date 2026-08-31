#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

archive="${1:?usage: restore.sh /var/backups/wappos/wappos_portal/wappos_portal-<stamp>.tar.gz}"

if ! id "$app" >/dev/null 2>&1; then
    useradd --system --home-dir "$install_dir" --shell /usr/sbin/nologin "$app"
fi

systemctl stop "$app" 2>/dev/null || true

tar -xzf "$archive" -C /

chown -R "$app:$app" "$install_dir"
chmod 750 "$install_dir"

systemctl daemon-reload
systemctl enable "$app"
systemctl restart "$app"

nginx -t && systemctl reload nginx

echo "wappos_portal restaure depuis $archive"
