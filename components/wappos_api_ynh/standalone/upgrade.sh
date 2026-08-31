#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

if [ -d "$pkg_dir/sources/tests" ]; then
    "$venv_dir/bin/pip" install -q -r "$pkg_dir/sources/requirements-dev.txt"
    if ! (cd "$pkg_dir/sources" && "$venv_dir/bin/python3" -m pytest -q); then
        echo "Tests en echec, deploiement annule."
        exit 1
    fi
fi

systemctl stop "$app" 2>/dev/null || true

rsync -a --delete --exclude=venv --exclude=.package --exclude=data "$pkg_dir/sources/" "$install_dir/"

mkdir -p "$install_dir/.package"
cp "$pkg_dir/manifest.toml" "$install_dir/.package/manifest.toml"

"$venv_dir/bin/pip" install --upgrade pip
"$venv_dir/bin/pip" install -r "$install_dir/requirements.txt"

chown -R "$app:$app" "$install_dir"
chmod 750 "$install_dir"

sed "s/__APP__/$app/g" "$pkg_dir/standalone/conf/wappos_api_du.sudoers" > "/etc/sudoers.d/${app}_du"
chmod 440 "/etc/sudoers.d/${app}_du"
chown root:root "/etc/sudoers.d/${app}_du"
visudo -c -f "/etc/sudoers.d/${app}_du"

sed -e "s/__APP__/$app/g" -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.service" > "/etc/systemd/system/$app.service"
sed -e "s/__APP__/$app/g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.socket" > "/etc/systemd/system/$app.socket"
sed -e "s/__APP__/$app/g" -e "s#__INSTALL_DIR__#$install_dir#g" \
    "$pkg_dir/standalone/conf/wappos_api_disk_cache.cron" > "/etc/cron.d/${app}-disk-cache"
systemctl daemon-reload
systemctl enable --now "$app.socket"

systemctl start "$app"

echo "wappos_api mis a jour (standalone)."
