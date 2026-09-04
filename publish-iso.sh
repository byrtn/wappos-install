#!/bin/bash
# Auteur : Patrick Ritaine
# A executer sur le Beelink (necessite gh CLI installe et authentifie une fois : gh auth login).
# Publie l'ISO deja construite comme fichier telechargeable sur le depot public,
# sous une release "latest" toujours a jour (meme lien de telechargement a chaque republication).
set -euo pipefail

ISO="/var/lib/vz/template/iso/wappos-debian-preseed.iso"
REPO="byrtn/wappos-install"
TAG="latest"

if [ ! -f "$ISO" ]; then
    echo "ISO introuvable : $ISO (lancer build-iso.sh d'abord)"
    exit 1
fi

command -v gh >/dev/null 2>&1 || { echo "gh CLI non installe. Voir https://cli.github.com/"; exit 1; }

if gh release view "$TAG" --repo "$REPO" >/dev/null 2>&1; then
    echo "Mise a jour de la release existante..."
    gh release upload "$TAG" "$ISO" --repo "$REPO" --clobber
else
    echo "Creation de la release..."
    gh release create "$TAG" "$ISO" --repo "$REPO" \
        --title "ISO Wappos (derniere version)" \
        --notes "ISO Debian 12 preconfiguree pour installer Wappos automatiquement. Demarrer dessus, repondre aux questions Debian standards (langue, clavier, fuseau horaire, partitionnement, nom d'hote), le reste s'installe tout seul."
fi

echo
echo "Publiee : https://github.com/$REPO/releases/download/$TAG/wappos-debian-preseed.iso"
