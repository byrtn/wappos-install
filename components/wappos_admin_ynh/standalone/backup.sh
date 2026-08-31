#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

backup_dir="/var/backups/wappos/$app"
retention="${WAPPOS_BACKUP_RETENTION:-7}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$backup_dir/$app-$stamp.tar.gz"
docker_volumes_tmp_dir="$install_dir/data/docker-volumes-backup"

mkdir -p "$backup_dir"

rm -rf "$docker_volumes_tmp_dir"
mkdir -p "$docker_volumes_tmp_dir"
"$venv_dir/bin/python3" -c "
import sys
sys.path.insert(0, '$install_dir')
import docker_gate
for r in docker_gate.backup_docker_volumes('$docker_volumes_tmp_dir'):
    print(r)
" || echo "Sauvegarde des volumes Docker Gate ignoree (Docker indisponible ou aucune app Docker)."

paths_to_backup=("${install_dir#/}" "etc/systemd/system/$app.service" "etc/cron.d/${app}-config-guard" "etc/sudoers.d/wappos_admin_docker_ce" "etc/yunohost/hooks.d/post_domain_add/50-$app")
for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
    frag="/etc/nginx/conf.d/${existing_domain}.d/wappos_admin_crossdomain.conf"
    [ -f "$frag" ] && paths_to_backup+=("${frag#/}")
done

tar -czf "$archive" -C / "${paths_to_backup[@]}"

rm -rf "$docker_volumes_tmp_dir"

ls -1t "$backup_dir"/"$app"-*.tar.gz | tail -n +$((retention + 1)) | xargs -r rm -f

echo "Sauvegarde ecrite : $archive"
