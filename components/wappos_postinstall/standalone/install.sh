#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

if ! id "$app" >/dev/null 2>&1; then
    useradd --system --home-dir "$install_dir" --shell /usr/sbin/nologin "$app"
fi

apt-get install -y python3-venv python3-pip

mkdir -p "$install_dir"
cp -ar "$pkg_dir/sources/." "$install_dir/"

mkdir -p "$install_dir/.package"
cp "$pkg_dir/manifest.toml" "$install_dir/.package/manifest.toml"

python3 -m venv "$venv_dir"
"$venv_dir/bin/pip" install --upgrade pip
"$venv_dir/bin/pip" install -r "$install_dir/requirements.txt"

chown -R "$app:$app" "$install_dir"
chmod 750 "$install_dir"

sed "s/__APP__/$app/g" "$pkg_dir/standalone/conf/wappos_postinstall_yunohost.sudoers" > /etc/sudoers.d/wappos_postinstall_yunohost
chmod 440 /etc/sudoers.d/wappos_postinstall_yunohost
chown root:root /etc/sudoers.d/wappos_postinstall_yunohost
visudo -c -f /etc/sudoers.d/wappos_postinstall_yunohost

sed -e "s/__APP__/$app/g" -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.service" > "/etc/systemd/system/$app.service"
sed -e "s/__APP__/$app/g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.socket" > "/etc/systemd/system/$app.socket"
systemctl daemon-reload
systemctl enable --now "$app.socket"
systemctl enable "$app"
systemctl restart "$app"

# Prend la place de l'ecran de postinstall natif YunoHost sur l'acces par IP
# brute (aucun domaine n'existe encore a ce stade). Sera naturellement
# remplace par /wappos-portal/ une fois le domaine cree (hooks post_domain_add
# deja existants de wappos_portal_ynh/wappos_sso_bypass, meme fichier cible).
mkdir -p /etc/nginx/conf.d/default.d
sed "s/__PORT__/$port/g" "$pkg_dir/standalone/conf/redirect_to_admin.conf" > /etc/nginx/conf.d/default.d/redirect_to_admin.conf
nginx -t && systemctl reload nginx

# S'auto-desactive des qu'un domaine est cree (voir sources/hooks/50-post_domain_add).
mkdir -p /etc/yunohost/hooks.d/post_domain_add
sed "s/__APP__/$app/g" "$pkg_dir/sources/hooks/50-post_domain_add" > "/etc/yunohost/hooks.d/post_domain_add/50-$app"
chmod 755 "/etc/yunohost/hooks.d/post_domain_add/50-$app"

echo "wappos_postinstall installe (standalone, hors systeme d'apps YunoHost)."
