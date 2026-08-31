#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

backup_dir="/var/backups/wappos/$app"
retention="${WAPPOS_BACKUP_RETENTION:-7}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$backup_dir/$app-$stamp.tar.gz"

mkdir -p "$backup_dir"

paths_to_backup=("${install_dir#/}" "etc/systemd/system/$app.service" "etc/cron.d/$app" "etc/yunohost/hooks.d/post_domain_add/50-$app")
for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
    frag="/etc/nginx/conf.d/${existing_domain}.d/${app}_crossdomain.conf"
    [ -f "$frag" ] && paths_to_backup+=("${frag#/}")
done

tar -czf "$archive" -C / "${paths_to_backup[@]}"

ls -1t "$backup_dir"/"$app"-*.tar.gz | tail -n +$((retention + 1)) | xargs -r rm -f

echo "Sauvegarde ecrite : $archive"
