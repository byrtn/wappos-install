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
    echo "Aucune action requise ici. Une adresse fixe pourra etre proposee a la fin"
    echo "de cette installation, une fois Wappos en place."
    touch "$network_configured_marker"
fi

step "Attente du reseau"
tries=0
until getent hosts install.yunohost.org >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "$tries" -ge 30 ]; then
        break
    fi
    sleep 2
done

if ! command -v curl >/dev/null 2>&1 || ! command -v rsync >/dev/null 2>&1; then
    apt-get update
    apt-get install -y curl rsync
fi

if ! command -v yunohost >/dev/null 2>&1; then
    step "Installation du coeur YunoHost"
    tries=0
    until curl https://install.yunohost.org | bash -s -- -a; do
        tries=$((tries + 1))
        if [ "$tries" -ge 4 ]; then
            echo "Echec apres plusieurs tentatives, abandon."
            exit 1
        fi
        echo
        echo "Echec, nouvelle tentative dans 10 secondes (${tries}/4)..."
        sleep 10
    done
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

if [ ! -f /etc/systemd/system/docker.service.d/nftables-resync.conf ]; then
    step "Protection Docker contre les rechargements nftables"
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/nftables-resync.conf <<'NFTABLES_EOF'
[Unit]
PartOf=nftables.service
StartLimitIntervalSec=120
StartLimitBurst=5

[Service]
ExecStartPre=/bin/sleep 5
Restart=on-failure
RestartSec=10
NFTABLES_EOF
    systemctl daemon-reload
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

if ! yunohost app list --output-as json | python3 -c "import json,sys; sys.exit(0 if 'rspamd' in [a['id'] for a in json.load(sys.stdin)['apps']] else 1)"; then
    step "Installation de Rspamd (antispam)"
    yunohost app install rspamd

    cat > /etc/rspamd/local.d/phishing.conf <<'RSPAMD_PHISHING_EOF'
openphish_enabled = true;
RSPAMD_PHISHING_EOF

    rspamd_password="$(openssl rand -base64 24)"
    rspamd_password_hash="$(rspamadm pw -p "$rspamd_password")"
    printf 'password = "%s";\n' "$rspamd_password_hash" > /etc/rspamd/local.d/worker-controller.inc

    rspamadm configtest
    systemctl reload rspamd
fi

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

chage -d 0 root

step "Connexion SSH par mot de passe"
echo "Par defaut, la connexion root en SSH accepte un mot de passe en plus"
echo "des cles. Pour un serveur expose sur Internet, il est recommande de"
echo "n'accepter que les cles SSH (plus resistant aux attaques par force brute)."
echo
if [ -s /root/.ssh/authorized_keys ]; then
    echo -e "${bold}Une cle SSH est deja enregistree pour root.${reset} Desactiver la connexion"
    echo "par mot de passe maintenant ? [o/N]"
    read -rp "> " disable_ssh_password

    if [ "$disable_ssh_password" = "o" ] || [ "$disable_ssh_password" = "O" ]; then
        cp /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak-$(date +%Y%m%d)"
        sed -i 's/^#\?PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
        sshd -t
        systemctl reload sshd
        echo -e "${bold}Connexion par mot de passe desactivee.${reset} Seules les cles SSH sont acceptees desormais."
    fi
else
    echo -e "${bold}Aucune cle SSH enregistree pour root${reset} — desactiver le mot de passe vous"
    echo "empecherait de vous reconnecter. Ajoutez d'abord votre cle publique a"
    echo "/root/.ssh/authorized_keys, puis relancez cette etape plus tard si besoin."
fi
echo

interface="$(ip route show default | awk '{print $5; exit}')"
current_ip="$(ip -4 -o addr show dev "$interface" | awk '{print $4}' | cut -d/ -f1 | head -n1)"

step "Adresse IP"
echo -e "Votre IP est ${bold}$current_ip${reset}, definie en DHCP (attribuee automatiquement"
echo "par votre routeur, elle peut changer a l'avenir)."
echo
echo -e "${bold}Nous conseillons une IP fixe pour un serveur.${reset} Souhaitez-vous la parametrer"
echo "maintenant ? [o/N]"
read -rp "> " set_static_ip

if [ "$set_static_ip" = "o" ] || [ "$set_static_ip" = "O" ]; then
    echo
    read -rp "Adresse IP fixe (ex. 192.168.1.201) : " static_ip
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

    title "IMPORTANT AVANT DE CONTINUER"
    echo -e "${bold}Cette connexion va se couper dans quelques secondes.${reset} C'est normal."
    echo
    echo -e "Reconnectez-vous ensuite avec : ${bold}ssh root@$static_ip${reset}"
    echo "Aucune autre action n'est necessaire, l'installation est deja terminee."
    echo
    read -rp "Appuyez sur Entree pour appliquer la nouvelle adresse : " _

    systemctl restart networking
    exit 0
fi
echo
