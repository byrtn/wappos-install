#!/bin/bash
set -eu
pkg_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

mkdir -p /etc/yunohost/hooks.d/post_domain_add
install -m 755 "$pkg_dir/sources/hooks/50-post_domain_add" /etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass

for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
    bash /etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass "$existing_domain"
done

echo "wappos_sso_bypass installe (protection permanente, jamais retiree par un install/remove d'autre composant)."
