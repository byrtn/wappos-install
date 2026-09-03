#!/bin/bash
set -eu
pkg_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p /usr/local/lib/wappos_sso_bypass
install -m 644 "$pkg_dir/sources/regen_bypass_conf.py" /usr/local/lib/wappos_sso_bypass/regen_bypass_conf.py

mkdir -p /etc/yunohost/hooks.d/post_domain_add
install -m 755 "$pkg_dir/sources/hooks/50-post_domain_add" /etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass

mkdir -p /etc/yunohost/hooks.d/post_domain_remove
install -m 755 "$pkg_dir/sources/hooks/50-post_domain_remove" /etc/yunohost/hooks.d/post_domain_remove/50-wappos-sso-bypass

mkdir -p /etc/yunohost/hooks.d/post_app_install
install -m 755 "$pkg_dir/sources/hooks/post_app_install" /etc/yunohost/hooks.d/post_app_install/50-wappos-sso-bypass

mkdir -p /etc/yunohost/hooks.d/post_app_remove
install -m 755 "$pkg_dir/sources/hooks/post_app_remove" /etc/yunohost/hooks.d/post_app_remove/50-wappos-sso-bypass

mkdir -p /etc/yunohost/hooks.d/post_app_change_url
install -m 755 "$pkg_dir/sources/hooks/post_app_change_url" /etc/yunohost/hooks.d/post_app_change_url/50-wappos-sso-bypass

bash /etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass

mkdir -p /etc/yunohost/hooks.d/conf_regen
install -m 755 "$pkg_dir/sources/hooks/conf_regen/60-restrict-portalapi" /etc/yunohost/hooks.d/conf_regen/60-restrict-portalapi
bash /etc/yunohost/hooks.d/conf_regen/60-restrict-portalapi

echo "wappos_sso_bypass installe (protection permanente, jamais retiree par un install/remove d'autre composant)."
