#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

backup_dir="/var/backups/wappos/$app"
retention="${WAPPOS_BACKUP_RETENTION:-7}"
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
archive="$backup_dir/$app-$stamp.tar.gz"

mkdir -p "$backup_dir"

tar -czf "$archive" \
    -C / \
    "${install_dir#/}" \
    "etc/systemd/system/$app.service"

ls -1t "$backup_dir"/"$app"-*.tar.gz | tail -n +$((retention + 1)) | xargs -r rm -f

echo "Sauvegarde ecrite : $archive"
