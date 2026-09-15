#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

for wapp in photos text office notes forms spreed groupfolders files_sharing files_versions files_trashbin files_external camerarawpreviews dashboard recommendations; do
    sudo -u nextcloud php /var/www/nextcloud/occ app:disable "$wapp" >/dev/null 2>&1 || true
done
