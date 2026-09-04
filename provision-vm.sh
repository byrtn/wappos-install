#!/bin/bash
# Auteur : Patrick Ritaine
# A executer sur l'hyperviseur Proxmox (root). Usage : ./provision-vm.sh <vmid>
set -euo pipefail

VMID="${1:?Usage: provision-vm.sh <vmid>}"
ISO="local:iso/wappos-debian-preseed.iso"

echo "=== Provisioning Wappos sur la VM $VMID ==="
echo

qm stop "$VMID" >/dev/null 2>&1 || true

echo "Remise a zero du disque..."
qm set "$VMID" --delete scsi0 >/dev/null 2>&1 || true
qm set "$VMID" --scsi0 local-lvm:40,iothread=1
qm set "$VMID" --delete unused0 >/dev/null 2>&1 || true
qm set "$VMID" --delete unused1 >/dev/null 2>&1 || true
qm set "$VMID" --delete unused2 >/dev/null 2>&1 || true

qm set "$VMID" --ide2 "$ISO,media=cdrom"
qm set "$VMID" --boot "order=scsi0;ide2"
qm start "$VMID"

echo "Installation Debian en cours (voir la console Proxmox pour suivre)..."
echo "Attente de l'extinction automatique de la VM..."

while true; do
    status="$(qm status "$VMID" | awk '{print $2}')"
    if [ "$status" = "stopped" ]; then
        break
    fi
    sleep 5
done

echo
echo "Debian est installe, la VM s'est eteinte comme prevu."
echo "Detachement du support d'installation et correction de l'ordre de demarrage..."

qm set "$VMID" --ide2 none
qm set "$VMID" --boot order=scsi0
qm start "$VMID"

echo
echo "=== VM $VMID redemarree sur le disque ==="
echo "Wappos s'installe maintenant tout seul, suivre la console Proxmox."
echo "A la fin, connexion possible sur https://<ip-de-la-vm>/wappos-portal/ et /wappos-admin/"
