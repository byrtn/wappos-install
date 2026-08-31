#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

archive="${1:?usage: restore.sh /var/backups/wappos/wappos_admin/wappos_admin-<stamp>.tar.gz}"

if ! id "$app" >/dev/null 2>&1; then
    useradd --system --home-dir "$install_dir" --shell /usr/sbin/nologin "$app"
fi

systemctl stop "$app" 2>/dev/null || true

tar -xzf "$archive" -C /

chown -R "$app:$app" "$install_dir"
chmod 750 "$install_dir"
chmod 440 /etc/sudoers.d/wappos_admin_docker_ce
chown root:root /etc/sudoers.d/wappos_admin_docker_ce
visudo -c -f /etc/sudoers.d/wappos_admin_docker_ce

if getent group docker >/dev/null 2>&1; then
    usermod -aG docker "$app"
fi

systemctl daemon-reload
systemctl enable "$app"
systemctl restart "$app"

nginx -t && systemctl reload nginx

docker_volumes_tmp_dir="$install_dir/data/docker-volumes-backup"
if [ -d "$docker_volumes_tmp_dir" ]; then
    "$venv_dir/bin/python3" -c "
import sys
sys.path.insert(0, '$install_dir')
import docker_gate
for r in docker_gate.restore_docker_volumes('$docker_volumes_tmp_dir'):
    print(r)
for r in docker_gate.restart_all_docker_apps():
    print(r)
" || echo "Restauration des volumes Docker Gate ignoree (Docker indisponible)."
    rm -rf "$docker_volumes_tmp_dir"
fi

echo "wappos_admin restaure depuis $archive"
