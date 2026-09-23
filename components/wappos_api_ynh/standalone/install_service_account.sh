#!/bin/bash
set -eu
source "$(dirname "${BASH_SOURCE[0]}")/vars.sh"

secret_path="/etc/yunohost/.wappos_api_service_secret"
owners_registry_path="/etc/yunohost/wappos_domain_owners.json"
primary_registry_path="/etc/yunohost/wappos_domain_admin_primary.json"
group_name="wappos_domain_admins"

if ! yunohost user group list --output-as json | grep -q "\"$group_name\""; then
    yunohost user group create "$group_name"
fi

if [ ! -f "$owners_registry_path" ]; then
    printf '{}' > "$owners_registry_path"
fi
chown "$app:$app" "$owners_registry_path"
chmod 640 "$owners_registry_path"

if [ ! -f "$primary_registry_path" ]; then
    printf '{}' > "$primary_registry_path"
fi
chown "$app:$app" "$primary_registry_path"
chmod 640 "$primary_registry_path"

if [ -f "$secret_path" ]; then
    exit 0
fi

service_user="wappos_svc_admin"
main_domain="$(yunohost domain list --output-as json | grep -o '"main": *"[^"]*"' | cut -d'"' -f4)"
service_password="$(head -c 48 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 40)"

yunohost user create "$service_user" -F "Wappos API" -p "$service_password" -d "$main_domain" -q 0
yunohost user group add admins "$service_user"

umask 077
printf '{"username": "%s", "password": "%s"}\n' "$service_user" "$service_password" > "$secret_path"
chown "$app:$app" "$secret_path"
chmod 600 "$secret_path"
