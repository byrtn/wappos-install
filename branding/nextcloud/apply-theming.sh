#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="/home/yunohost.app/nextcloud/data"
OCC="sudo -u nextcloud php /var/www/nextcloud/occ"

cp "$BRANDING_DIR/wappos-logo.png" "$DATA_DIR/wappos-logo.png"
cp "$BRANDING_DIR/wappos-favicon.png" "$DATA_DIR/wappos-favicon.png"
chown nextcloud:nextcloud "$DATA_DIR/wappos-logo.png" "$DATA_DIR/wappos-favicon.png"

$OCC theming:config name "Wappos - Cloud"
$OCC theming:config slogan "Souveraineté numérique"
$OCC theming:config primary_color "#016f93"
if [ -n "${1:-}" ]; then
    $OCC theming:config url "https://$1"
fi
$OCC theming:config logo "$DATA_DIR/wappos-logo.png"
$OCC theming:config logoheader "$DATA_DIR/wappos-logo.png"
$OCC theming:config favicon "$DATA_DIR/wappos-favicon.png"

rm -f "$DATA_DIR/wappos-logo.png" "$DATA_DIR/wappos-favicon.png"
