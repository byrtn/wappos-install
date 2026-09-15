#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKELETON_DIR="/home/yunohost.app/nextcloud/wappos-skeleton"

rm -rf "$SKELETON_DIR"
cp -r "$BRANDING_DIR/skeleton" "$SKELETON_DIR"
chown -R nextcloud:nextcloud "$SKELETON_DIR"

sudo -u nextcloud php /var/www/nextcloud/occ config:system:set skeletondirectory --value="$SKELETON_DIR"
