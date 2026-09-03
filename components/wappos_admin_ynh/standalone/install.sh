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

if getent group docker >/dev/null 2>&1; then
    usermod -aG docker "$app"
fi

sed "s/__APP__/$app/g" "$pkg_dir/standalone/conf/wappos_admin_docker_ce.sudoers" > /etc/sudoers.d/wappos_admin_docker_ce
chmod 440 /etc/sudoers.d/wappos_admin_docker_ce
chown root:root /etc/sudoers.d/wappos_admin_docker_ce
visudo -c -f /etc/sudoers.d/wappos_admin_docker_ce

sed "s/__APP__/$app/g" "$pkg_dir/standalone/conf/wappos_admin_security_monitor.sudoers" > /etc/sudoers.d/wappos_admin_security_monitor
chmod 440 /etc/sudoers.d/wappos_admin_security_monitor
chown root:root /etc/sudoers.d/wappos_admin_security_monitor
visudo -c -f /etc/sudoers.d/wappos_admin_security_monitor

sed -e "s/__APP__/$app/g" -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.service" > "/etc/systemd/system/$app.service"
sed -e "s/__APP__/$app/g" -e "s/__PORT__/$port/g" \
    "$pkg_dir/standalone/conf/systemd.socket" > "/etc/systemd/system/$app.socket"
systemctl daemon-reload
systemctl enable --now "$app.socket"
systemctl enable "$app"
systemctl restart "$app"

deploy_crossdomain_hook
deploy_maildir_hook
deploy_prometheus_readonly_user
deploy_backup_hooks
deploy_portal_branding_hook

cat > /usr/local/bin/wappos <<'WAPPOS_CLI_ALIAS'
#!/bin/sh
exec /usr/bin/yunohost "$@"
WAPPOS_CLI_ALIAS
chmod 755 /usr/local/bin/wappos

compute_admin_alert_mail
sed -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__ADMIN_ALERT_MAIL__/$admin_alert_mail/g" \
    "$pkg_dir/standalone/conf/wappos_admin_config_guard.cron" > "/etc/cron.d/${app}-config-guard"
sed -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__ADMIN_ALERT_MAIL__/$admin_alert_mail/g" \
    "$pkg_dir/standalone/conf/wappos_admin_backup_scheduler.cron" > "/etc/cron.d/${app}-backup-scheduler"
sed -e "s#__INSTALL_DIR__#$install_dir#g" -e "s/__ADMIN_ALERT_MAIL__/$admin_alert_mail/g" -e "s#__ALERT_MBOX__#$alert_box_mbox#g" \
    "$pkg_dir/standalone/conf/wappos_admin_mail_alert_filter.cron" > "/etc/cron.d/${app}-mail-alert-filter"
cp "$pkg_dir/standalone/conf/wappos_admin_diagnosis_cache.cron" "/etc/cron.d/${app}-diagnosis-cache"
cp "$pkg_dir/standalone/conf/wappos_admin_yunohost_log_purge.cron" "/etc/cron.d/${app}-yunohost-log-purge"
deploy_mail_alert_filter_config

echo "wappos_admin installe (standalone, hors systeme d'apps YunoHost)."
