#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

WWW="/var/www/roundcube"
BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="$WWW/config/config.inc.php"

if [ ! -d "$WWW" ]; then
    exit 0
fi

mkdir -p "$WWW/plugins/wappos_theme"
cp "$BRANDING_DIR/wappos_theme/wappos_theme.php" "$WWW/plugins/wappos_theme/wappos_theme.php"
cp "$BRANDING_DIR/wappos_theme/wappos-theme.css" "$WWW/plugins/wappos_theme/wappos-theme.css"
cp "$BRANDING_DIR/wappos_theme/Montserrat-Variable.woff2" "$WWW/plugins/wappos_theme/Montserrat-Variable.woff2"
cp "$BRANDING_DIR/wappos-logo.png" "$WWW/wappos-logo.png"

if [ -f "$CONFIG" ]; then
    sed -i "s#\$config\['product_name'\] = '[^']*';#\$config['product_name'] = 'Wappos Webmail';#" "$CONFIG"

    if ! grep -q "wappos_theme" "$CONFIG"; then
        sed -i "s#// installed plugins#'wappos_theme',\n    // installed plugins#" "$CONFIG"
    fi

    if ! grep -q "skin_logo" "$CONFIG"; then
        printf "\n\$config['skin_logo'] = 'wappos-logo.png';\n" >> "$CONFIG"
    fi

    sed -i "s#^\$config\['logout_url'\] = .*;#\$config['logout_url'] = 'https://' . \$main_domain . '/wappos-portal/';#" "$CONFIG"
fi
