app="wappos_admin"
install_dir="/opt/yunohost/$app"
venv_dir="$install_dir/venv"
port="9500"
pkg_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
alert_box_user="cron.alerts"
alert_box_mbox="/var/mail/$alert_box_user"

compute_admin_alert_mail() {
    main_domain="$(yunohost domain list --output-as json 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("main",""))' 2>/dev/null)"
    admin_alert_mail="$(yunohost user info adminynh --output-as json 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("mail",""))' 2>/dev/null)"
    if [ -z "$admin_alert_mail" ]; then
        admin_alert_mail="adminynh@$main_domain"
    fi
}

deploy_mail_alert_filter_config() {
    if [ -d "$alert_box_mbox" ]; then
        rm -rf "$alert_box_mbox"
        echo "Maildir de $alert_box_user supprime (boite technique livree en mbox via transport local, jamais utilisee en Maildir)"
    fi
    printf '%s@%s local:%s\n' "$alert_box_user" "$main_domain" "$alert_box_user" > /etc/postfix/transport
    postmap /etc/postfix/transport
    if ! postconf transport_maps | grep -q "hash:/etc/postfix/transport"; then
        postconf -e "transport_maps = hash:/etc/postfix/transport"
    fi
    systemctl reload postfix
    if [ -f /etc/default/rkhunter ]; then
        sed -i "s/^REPORT_EMAIL=.*/REPORT_EMAIL=\"$alert_box_user@$main_domain\"/" /etc/default/rkhunter
    fi
    if [ -f /etc/chkrootkit/chkrootkit.conf ]; then
        sed -i "s/^MAILTO=.*/MAILTO=\"$alert_box_user@$main_domain\"/" /etc/chkrootkit/chkrootkit.conf
    fi
}

prometheus_web_yml="/etc/prometheus/web.yml"
prometheus_ro_user="wappos_admin_ro"
prometheus_ro_password_file="$install_dir/.package/prometheus_password"

deploy_prometheus_readonly_user() {
    if [ ! -f "$prometheus_web_yml" ]; then
        return
    fi
    if ! command -v htpasswd >/dev/null 2>&1; then
        apt-get install -y apache2-utils >/dev/null 2>&1
    fi
    mkdir -p "$(dirname "$prometheus_ro_password_file")"
    if [ -f "$prometheus_ro_password_file" ]; then
        prometheus_ro_password="$(cat "$prometheus_ro_password_file")"
    else
        prometheus_ro_password="$(openssl rand -hex 24)"
        printf '%s' "$prometheus_ro_password" > "$prometheus_ro_password_file"
    fi
    chown "$app:$app" "$prometheus_ro_password_file"
    chmod 600 "$prometheus_ro_password_file"
    prometheus_ro_hash="$(htpasswd -nbBC 12 x "$prometheus_ro_password" | cut -d: -f2)"
    "$venv_dir/bin/python3" - "$prometheus_web_yml" "$prometheus_ro_user" "$prometheus_ro_hash" <<'PYEOF'
import sys
import yaml

path, user, pw_hash = sys.argv[1], sys.argv[2], sys.argv[3]
with open(path) as f:
    data = yaml.safe_load(f) or {}
users = data.setdefault("basic_auth_users", {})
users.pop("claude-readonly", None)
users[user] = pw_hash
with open(path, "w") as f:
    yaml.dump(data, f)
PYEOF
    systemctl reload prometheus 2>/dev/null || true
}

deploy_crossdomain_hook() {
    cp "$pkg_dir/sources/hooks/50-post_domain_add" "$install_dir/hooks/50-post_domain_add"
    chmod 755 "$install_dir/hooks/50-post_domain_add"
    mkdir -p /etc/yunohost/hooks.d/post_domain_add
    cp "$install_dir/hooks/50-post_domain_add" "/etc/yunohost/hooks.d/post_domain_add/50-$app"
    for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
        bash "$install_dir/hooks/50-post_domain_add" "$existing_domain"
    done
}

deploy_backup_hooks() {
    mkdir -p /etc/yunohost/hooks.d/backup /etc/yunohost/hooks.d/restore
    cp "$pkg_dir/sources/hooks/backup/60-wappos_data" /etc/yunohost/hooks.d/backup/60-wappos_data
    cp "$pkg_dir/sources/hooks/restore/60-wappos_data" /etc/yunohost/hooks.d/restore/60-wappos_data
    chmod 755 /etc/yunohost/hooks.d/backup/60-wappos_data /etc/yunohost/hooks.d/restore/60-wappos_data
}

deploy_maildir_hook() {
    cp "$pkg_dir/sources/hooks/50-post_user_create" "$install_dir/hooks/50-post_user_create"
    chmod 755 "$install_dir/hooks/50-post_user_create"
    mkdir -p /etc/yunohost/hooks.d/post_user_create
    cp "$install_dir/hooks/50-post_user_create" "/etc/yunohost/hooks.d/post_user_create/50-$app"
    yunohost user list --output-as json | python3 -c "import json,sys; d=json.load(sys.stdin)['users']; [print(f\"{username}\t{u['mail']}\") for username, u in d.items()]" \
    | while IFS="$(printf '\t')" read -r existing_username existing_mail; do
        if [ "$existing_username" = "$alert_box_user" ]; then
            continue
        fi
        mailbox_path="/var/mail/$existing_username"
        if [ -f "$mailbox_path" ]; then
            stray_path="${mailbox_path}.stray-$(date +%s)"
            mv "$mailbox_path" "$stray_path"
            echo "Maildir de $existing_username remplace par un mbox stray, deplace vers $stray_path"
        fi
        doveadm mailbox create -u "$existing_mail" INBOX || true
    done
}
