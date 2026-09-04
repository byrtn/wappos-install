#!/bin/bash
# Auteur : Patrick Ritaine
# A executer sur l'hyperviseur Proxmox (root). Usage : ./deploy.sh <vmid>
# Fait tout, de bout en bout, sans autre intervention : recupere le code a jour,
# reconstruit l'ISO, installe Debian+Wappos sur la VM indiquee.
set -euo pipefail

VMID="${1:?Usage: deploy.sh <vmid>}"
REPO_DIR="/root/wappos-install-src"

echo "=== Recuperation du code a jour ==="
if [ -d "$REPO_DIR/.git" ]; then
    git -C "$REPO_DIR" pull --ff-only
else
    git clone https://github.com/byrtn/wappos-install.git "$REPO_DIR"
fi

chmod +x "$REPO_DIR/build-iso.sh" "$REPO_DIR/provision-vm.sh"

echo
echo "=== Reconstruction de l'ISO ==="
"$REPO_DIR/build-iso.sh"

echo
echo "=== Installation sur la VM $VMID ==="
"$REPO_DIR/provision-vm.sh" "$VMID"
