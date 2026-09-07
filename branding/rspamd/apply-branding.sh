#!/bin/bash
# Auteur : Patrick Ritaine
# Applique l'habillage Wappos sur l'interface web native de Rspamd (logo,
# titre, couleurs). Idempotent - reexecutable a chaque fois sans effet de
# bord, y compris apres une mise a jour du paquet rspamd qui restaurerait
# les fichiers d'origine.
set -euo pipefail

WWW="/usr/share/rspamd/www"
BRANDING_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$WWW" ]; then
    exit 0
fi

cp "$BRANDING_DIR/rspamd_logo_navbar.png" "$WWW/img/rspamd_logo_navbar.png"
cp "$BRANDING_DIR/rspamd_logo_navbar_dark.png" "$WWW/img/rspamd_logo_navbar_dark.png"

mkdir -p "$WWW/fonts"
cp "$BRANDING_DIR/fonts/Montserrat-Variable.woff2" "$WWW/fonts/Montserrat-Variable.woff2"
cp "$BRANDING_DIR/wappos-theme.css" "$WWW/css/wappos-theme.css"

sed -i 's#<title>Rspamd Web Interface</title>#<title>Wappos — Antispam</title>#' "$WWW/index.html"

if ! grep -q 'wappos-theme.css' "$WWW/index.html"; then
    sed -i 's#<link href="./css/icons.css" rel="stylesheet">#<link href="./css/wappos-theme.css" rel="stylesheet">\n\t<link href="./css/icons.css" rel="stylesheet">#' "$WWW/index.html"
fi
