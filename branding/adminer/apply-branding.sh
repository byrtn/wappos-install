#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

WWW="/var/www/adminer"
BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$WWW" ]; then
    exit 0
fi

cp "$BRANDING_DIR/adminer.css" "$WWW/adminer.css"
cp "$BRANDING_DIR/adminer-dark.css" "$WWW/adminer-dark.css"
cp "$BRANDING_DIR/wappos-logo.png" "$WWW/wappos-logo.png"
cp "$BRANDING_DIR/wappos-logo-dark.png" "$WWW/wappos-logo-dark.png"
chown adminer:www-data "$WWW/adminer.css" "$WWW/adminer-dark.css" "$WWW/wappos-logo.png" "$WWW/wappos-logo-dark.png"
