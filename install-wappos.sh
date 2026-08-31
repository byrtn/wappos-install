#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$script_dir/components"
alert_box_user="cron.alerts"

network_configured_marker="$script_dir/.network-configured"

echo "=== Installeur Wappos ==="
echo

if [ ! -f "$network_configured_marker" ]; then
    echo "--- Configuration reseau ---"
    interface="$(ip route show default | awk '{print $5; exit}')"
    if [ -z "$interface" ]; then
        interface="$(ip -o link show | awk -F': ' '$2 != "lo" {print $2; exit}')"
    fi
    echo "Interface reseau detectee : $interface"
    echo
    echo "1) DHCP (automatique)"
    echo "2) IP statique (recommande pour un serveur)"
    read -rp "Choix [1/2] : " network_choice

    if [ "$network_choice" = "2" ]; then
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
        echo
        echo "IP statique configuree : $static_ip"
        echo "Si cette session est en SSH, elle risque de se couper au redemarrage du reseau."
        echo "Reconnectez-vous alors sur : $static_ip"
        sleep 3
        systemctl restart networking
        echo
        echo "Reseau redemarre. Relancez ce script pour continuer l'installation."
        exit 0
    else
        touch "$network_configured_marker"
        echo "DHCP conserve."
    fi
    echo
fi

if ! command -v curl >/dev/null 2>&1; then
    apt-get update
    apt-get install -y curl
fi

if ! command -v yunohost >/dev/null 2>&1; then
    echo "--- Installation du coeur YunoHost ---"
    curl https://install.yunohost.org | bash -s -- -a
fi

if [ ! -f /etc/yunohost/installed ]; then
    echo
    echo "--- Configuration initiale (domaine, mot de passe administrateur) ---"
    until yunohost tools postinstall -u adminynh; do
        echo
        echo "La configuration a echoue, reessayons."
        echo
    done
fi

echo
echo "YunoHost est installe et configure."

if ! command -v docker >/dev/null 2>&1; then
    echo
    echo "--- Installation de Docker Engine ---"
    curl -fsSL https://get.docker.com | sh
fi

main_domain="$(yunohost domain list --output-as json | python3 -c "import json,sys; print(json.load(sys.stdin)['main'])")"

if ! yunohost user list --output-as json | python3 -c "import json,sys; sys.exit(0 if '$alert_box_user' in json.load(sys.stdin)['users'] else 1)"; then
    echo
    echo "--- Creation du compte technique d'alertes ---"
    yunohost user create "$alert_box_user" -F "SYSTEME - NE PAS SUPPRIMER" -d "$main_domain" -p "$(openssl rand -base64 24)"
fi

echo
echo "--- Installation des composants Wappos ---"
for component in wappos_api_ynh wappos_sso_bypass wappos_admin_ynh wappos_portal_ynh prometheus_ynh; do
    echo "Installation de $component..."
    bash "$release_dir/$component/standalone/install.sh"
done

echo
echo "Wappos est installe."
