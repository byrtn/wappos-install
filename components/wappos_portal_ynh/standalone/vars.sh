app="wappos_portal"
install_dir="/opt/yunohost/$app"
venv_dir="$install_dir/venv"
port="9300"
url_path="wappos-portal"
pkg_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

compute_admin_alert_mail() {
    admin_alert_mail="$(yunohost user info adminynh --output-as json 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("mail",""))' 2>/dev/null)"
    if [ -z "$admin_alert_mail" ]; then
        main_domain="$(yunohost domain list --output-as json 2>/dev/null \
            | python3 -c 'import json,sys; print(json.load(sys.stdin).get("main",""))' 2>/dev/null)"
        admin_alert_mail="adminynh@$main_domain"
    fi
}

deploy_crossdomain_hook() {
    sed -e "s/__PORT__/$port/g" -e "s/__APP__/$app/g" -e "s/__URL_PATH__/$url_path/g" \
        "$pkg_dir/sources/hooks/50-post_domain_add" > "$install_dir/hooks/50-post_domain_add"
    chmod 755 "$install_dir/hooks/50-post_domain_add"
    mkdir -p /etc/yunohost/hooks.d/post_domain_add
    cp "$install_dir/hooks/50-post_domain_add" "/etc/yunohost/hooks.d/post_domain_add/50-$app"
    for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
        bash "$install_dir/hooks/50-post_domain_add" "$existing_domain"
    done

    sed -e "s/__APP__/$app/g" \
        "$pkg_dir/sources/hooks/50-post_domain_remove" > "$install_dir/hooks/50-post_domain_remove"
    chmod 755 "$install_dir/hooks/50-post_domain_remove"
    mkdir -p /etc/yunohost/hooks.d/post_domain_remove
    cp "$install_dir/hooks/50-post_domain_remove" "/etc/yunohost/hooks.d/post_domain_remove/50-$app"
}
