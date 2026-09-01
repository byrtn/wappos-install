#!/bin/bash
# Auteur : Patrick Ritaine
# A executer sur l'hyperviseur Proxmox (root), la ou l'ISO Debian netinst est deja stockee.
set -euo pipefail

SRC_ISO="${1:-/var/lib/vz/template/iso/debian-12.15.0-amd64-netinst.iso}"
OUT_ISO="${2:-/var/lib/vz/template/iso/wappos-debian-preseed.iso}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PRESEED_SRC="$SCRIPT_DIR/preseed.cfg"
WORKDIR="/tmp/wappos-iso-build"

if [ ! -f "$SRC_ISO" ]; then
    echo "ISO source introuvable : $SRC_ISO"
    exit 1
fi
if [ ! -f "$PRESEED_SRC" ]; then
    echo "preseed.cfg introuvable a cote de ce script : $PRESEED_SRC"
    exit 1
fi

command -v xorriso >/dev/null 2>&1 || apt-get install -y xorriso
[ -f /usr/lib/ISOLINUX/isohdpfx.bin ] || apt-get install -y isolinux

rm -rf "$WORKDIR"
mkdir -p "$WORKDIR/mnt" "$WORKDIR/iso"

mount -o loop,ro "$SRC_ISO" "$WORKDIR/mnt"
rsync -a "$WORKDIR/mnt/" "$WORKDIR/iso/"
umount "$WORKDIR/mnt"

cp "$PRESEED_SRC" "$WORKDIR/iso/preseed.cfg"

cat > "$WORKDIR/iso/isolinux/isolinux.cfg" << 'EOF'
default auto
prompt 0
timeout 1

label auto
  kernel /install.amd/vmlinuz
  append auto=true priority=critical vga=788 initrd=/install.amd/initrd.gz preseed/file=/cdrom/preseed.cfg --- quiet
EOF

cd "$WORKDIR/iso"
find . -type f ! -name md5sum.txt -exec md5sum {} \; > md5sum.txt

xorriso -as mkisofs \
    -r -J -joliet-long \
    -V "WAPPOS_AUTO" \
    -isohybrid-mbr /usr/lib/ISOLINUX/isohdpfx.bin \
    -c isolinux/boot.cat \
    -b isolinux/isolinux.bin -no-emul-boot -boot-load-size 4 -boot-info-table \
    -eltorito-alt-boot \
    -e boot/grub/efi.img -no-emul-boot -isohybrid-gpt-basdat \
    -o "$OUT_ISO" \
    "$WORKDIR/iso"

echo
echo "ISO cree : $OUT_ISO"
