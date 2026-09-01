#!/bin/bash
set -eu

echo "ATTENTION : ce script retire la protection permanente anti-SSO-natif de tous les domaines."
echo "Ce n'est jamais invoque automatiquement par aucun autre composant Wappos."
read -r -p "Confirmer la suppression (taper OUI en majuscules) : " confirm
if [ "$confirm" != "OUI" ]; then
    echo "Annule."
    exit 1
fi

rm -f /etc/yunohost/hooks.d/post_domain_add/50-wappos-sso-bypass
rm -f /etc/yunohost/hooks.d/post_domain_remove/50-wappos-sso-bypass

for existing_domain in $(yunohost domain list --output-as json | python3 -c "import json,sys; print('\n'.join(json.load(sys.stdin)['domains']))"); do
    rm -f "/etc/nginx/conf.d/${existing_domain}.d/wappos_sso_bypass.conf"
done
nginx -t && systemctl reload nginx

echo "wappos_sso_bypass retire."
