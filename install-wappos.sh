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
    interface="$(ip route show default | awk '{print $5; exit}')"
    if [ -z "$interface" ]; then
        interface="$(ip -o link show | awk -F': ' '$2 != "lo" {print $2; exit}')"
    fi
    echo "Interface reseau detectee : $interface"
    echo
    echo -e "  ${bold}1)${reset} DHCP (automatique)"
    echo -e "  ${bold}2)${reset} IP statique (recommande pour un serveur)"
    echo
    read -rp "Choix [1/2] : " network_choice

    if [ "$network_choice" = "2" ]; then
        echo
        read -rp "Adresse IP (ex. 192.168.1.201) : " static_ip
        read -rp "Masque de sous-reseau (ex. 255.255.255.0) : " static_netmask
        read -rp "Passerelle (ex. 192.168.1.254) : " static_gateway
        read -rp "Serveur DNS (ex. 192.168.1.254) : " static_dns

        cat > /etc/network/interfaces << NETEOF
source /etc/network/interfaces.d/*

auto lo
iface lo inet loopback

allow-hotplug $interface
iface $interface inet static
    address $static_ip
    netmask $static_netmask
    gateway $static_gateway
    dns-nameservers $static_dns

iface $interface inet6 auto
NETEOF

        touch "$network_configured_marker"
        title "IP statique configuree : $static_ip"
        echo -e "${bold}A FAIRE MAINTENANT :${reset}"
        echo
        echo "  1. Attendez 10 secondes."
        echo "  2. Fermez cette connexion (elle va se couper toute seule)."
        echo -e "  3. Reconnectez-vous avec : ${bold}ssh root@$static_ip${reset}"
        echo
        echo "     Si votre ordinateur affiche un avertissement du type"
        echo "     'REMOTE HOST IDENTIFICATION HAS CHANGED' : ce n'est pas"
        echo "     un piratage, c'est normal ici (nouvelle machine ou nouvelle"
        echo "     installation utilisant cette meme adresse IP). Suivez"
        echo "     simplement la commande que votre terminal vous propose"
        echo "     pour oublier l'ancienne cle, puis reconnectez-vous."
        echo
        echo -e "  4. Relancez ce meme script : ${bold}$script_dir/install-wappos.sh${reset}"
        echo
        (sleep 2 && systemctl restart networking) >/dev/null 2>&1 &
        disown
        exit 0
    else
        touch "$network_configured_marker"
        echo
        echo "DHCP conserve."
    fi
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
