#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

systemctl stop "$app" 2>/dev/null || true

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL -o "$tmp_dir/$prometheus_tarball" "$prometheus_url"
echo "${prometheus_sha256}  $tmp_dir/$prometheus_tarball" | sha256sum -c -
tar -xzf "$tmp_dir/$prometheus_tarball" -C "$tmp_dir"

extracted_dir="$tmp_dir/prometheus-${prometheus_version}.linux-amd64"
cp "$extracted_dir/prometheus" "$extracted_dir/promtool" "$install_dir/"

token_admin="$(cat /opt/yunohost/wappos_admin/.package/metrics_token)"
token_portal="$(cat /opt/yunohost/wappos_portal/.package/metrics_token)"
token_api="$(cat /opt/yunohost/wappos_api/.package/metrics_token)"

sed -e "s/__TOKEN_ADMIN__/$token_admin/g" -e "s/__TOKEN_PORTAL__/$token_portal/g" -e "s/__TOKEN_API__/$token_api/g" \
    "$pkg_dir/standalone/conf/prometheus.yml" > "$config_dir/prometheus.yml"

if [ ! -f "$config_dir/web.yml" ]; then
    basic_auth_password="$(openssl rand -base64 24)"
    basic_auth_hash="$(python3 -c "import crypt,sys; print(crypt.crypt(sys.argv[1], crypt.mksalt(crypt.METHOD_BLOWFISH)))" "$basic_auth_password")"
    cat > "$config_dir/web.yml" <<WEBYML
basic_auth_users:
  admin: $basic_auth_hash
WEBYML
    echo "$basic_auth_password" > "$config_dir/basic_auth_password"
    echo "nouveau mot de passe basic auth (utilisateur admin) : $basic_auth_password"
fi

chown -R "$app:$app" "$install_dir" "$data_dir"
chown root:"$app" "$config_dir" "$config_dir/prometheus.yml" "$config_dir/web.yml"
chmod 750 "$config_dir"
chmod 640 "$config_dir/prometheus.yml" "$config_dir/web.yml"
chmod 600 "$config_dir/basic_auth_password"

sed -e "s/__APP__/$app/g" -e "s#__INSTALL_DIR__#$install_dir#g" -e "s#__CONFIG_DIR__#$config_dir#g" \
    -e "s#__DATA_DIR__#$data_dir#g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.service" > "/etc/systemd/system/$app.service"
systemctl daemon-reload
systemctl start "$app"

echo "prometheus mis a jour (standalone)."
