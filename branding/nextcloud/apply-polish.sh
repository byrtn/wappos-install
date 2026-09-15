#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPS_DIR="/var/www/nextcloud/apps"
OCC="sudo -u nextcloud php /var/www/nextcloud/occ"

rm -rf "$APPS_DIR/wappos_polish"
cp -r "$BRANDING_DIR/wappos_polish" "$APPS_DIR/wappos_polish"
chown -R nextcloud:www-data "$APPS_DIR/wappos_polish"

$OCC app:enable wappos_polish
