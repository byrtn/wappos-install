#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

bold="\033[1m"
reset="\033[0m"

title() {
    echo
    echo -e "${bold}================================================${reset}"
    echo -e "${bold}$1${reset}"
    echo -e "${bold}================================================${reset}"
    echo
}

step() {
    echo
    echo -e "${bold}--- $1 ---${reset}"
    echo
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$script_dir/components"
alert_box_user="cron.alerts"

network_configured_marker="$script_dir/.network-configured"

title "Installeur Wappos"

if [ ! -f "$network_configured_marker" ]; then
    step "Configuration reseau"
    echo "Ce serveur utilise l'adresse IP fournie automatiquement par votre routeur (DHCP)."
    echo "Aucune action requise ici."
    echo
    echo "Pour lui donner une adresse fixe, faites-le APRES l'installation, depuis"
    echo "l'interface d'administration Wappos (menu Reseau) une fois connecte."
    touch "$network_configured_marker"
fi

if ! command -v curl >/dev/null 2>&1 || ! command -v rsync >/dev/null 2>&1; then
    apt-get update
    apt-get install -y curl rsync
fi

if ! command -v yunohost >/dev/null 2>&1; then
    step "Installation du coeur YunoHost"
    curl https://install.yunohost.org | bash -s -- -a
fi

if [ ! -f /etc/yunohost/installed ]; then
    title "Configuration initiale"
    echo "Les questions suivantes vous demandent :"
    echo
    echo -e "  ${bold}- le nom de domaine${reset} de votre serveur"
    echo -e "  ${bold}- un mot de passe administrateur${reset} (robuste, evitez les mots courants)"
    echo -e "  ${bold}- d'accepter les conditions d'utilisation${reset} de YunoHost"
    echo
    until yunohost tools postinstall -u adminynh -F "Administrateur"; do
        echo
        echo -e "${bold}Echec, on recommence ces memes questions.${reset}"
        echo
    done
fi

step "YunoHost est installe et configure"

if ! command -v docker >/dev/null 2>&1; then
    step "Installation de Docker Engine"
    curl -fsSL https://get.docker.com | sh
fi

main_domain="$(yunohost domain list --output-as json | python3 -c "import json,sys; print(json.load(sys.stdin)['main'])")"

if ! yunohost user list --output-as json | python3 -c "import json,sys; sys.exit(0 if '$alert_box_user' in json.load(sys.stdin)['users'] else 1)"; then
    step "Creation du compte technique d'alertes"
    yunohost user create "$alert_box_user" -F "SYSTEME - NE PAS SUPPRIMER" -d "$main_domain" -p "$(openssl rand -base64 24)"
fi

step "Installation des composants Wappos"
for component in wappos_api_ynh wappos_sso_bypass wappos_admin_ynh wappos_portal_ynh prometheus_ynh; do
    echo -e "${bold}Installation de $component...${reset}"
    bash "$release_dir/$component/standalone/install.sh"
    echo
done

step "Finalisation de la liaison Prometheus / wappos_admin"
(
    source "$release_dir/wappos_admin_ynh/standalone/vars.sh"
    deploy_prometheus_readonly_user
)
systemctl restart wappos_admin

title "Installation terminee"
echo -e "${bold}Wappos est installe et pret a l'usage.${reset}"
echo
echo -e "  Portail        : ${bold}https://$main_domain/wappos-portal/${reset}"
echo -e "  Administration : ${bold}https://$main_domain/wappos-admin/${reset}"
echo
