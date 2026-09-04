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

if [ ! -f "$WORKDIR/iso/install.amd/gtk/vmlinuz" ] || [ ! -f "$WORKDIR/iso/install.amd/gtk/initrd.gz" ]; then
    echo "Noyau/initrd graphique introuvable a l'emplacement attendu (install.amd/gtk/) sur cette ISO."
    echo "Contenu de install.amd/ :"
    ls -la "$WORKDIR/iso/install.amd/" 2>/dev/null || echo "(dossier install.amd/ absent)"
    exit 1
fi

BRANDING_DIR="$SCRIPT_DIR/branding"
if [ -f "$BRANDING_DIR/logo_debian.png" ] && [ -f "$BRANDING_DIR/logo_debian_dark.png" ]; then
    echo "Remplacement du logo Debian par le logo Wappos dans l'installeur graphique..."
    INITRD_GTK="$WORKDIR/iso/install.amd/gtk/initrd.gz"
    INITRD_WORK="$WORKDIR/initrd-rebuild"
    rm -rf "$INITRD_WORK"
    mkdir -p "$INITRD_WORK"
    ( cd "$INITRD_WORK" && zcat "$INITRD_GTK" | cpio -idm --no-absolute-filenames 2>/dev/null )
    cp "$BRANDING_DIR/logo_debian.png" "$INITRD_WORK/usr/share/graphics/logo_debian.png"
    cp "$BRANDING_DIR/logo_debian_dark.png" "$INITRD_WORK/usr/share/graphics/logo_debian_dark.png"

    echo "Remplacement de la couleur de selection (turquoise Debian) par le bleu Wappos..."
    GTKRC="$INITRD_WORK/usr/share/themes/Clearlooks/gtk-2.0/gtkrc"
    if [ -f "$GTKRC" ]; then
        sed -i 's/#298d85/#016f93/g' "$GTKRC"
    fi

    ( cd "$INITRD_WORK" && find . | cpio -o -H newc 2>/dev/null | gzip -9 ) > "$INITRD_GTK"
fi

cat > "$WORKDIR/iso/isolinux/isolinux.cfg" << 'EOF'
default auto
prompt 0
timeout 1

label auto
  kernel /install.amd/gtk/vmlinuz
  append vga=788 initrd=/install.amd/gtk/initrd.gz preseed/file=/cdrom/preseed.cfg debian-installer/exit/poweroff=true ---
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
