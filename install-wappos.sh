#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

bold="\033[1m"
reset="\033[0m"
blue="\033[1;36m"
green="\033[1;32m"
red="\033[1;31m"
yellow="\033[1;33m"

step_count=0
TOTAL_STEPS=12

banner() {
    echo
    echo -e "${blue}════════════════════════════════════════════════════════════${reset}"
    echo -e "${blue}${bold}                        W A P P O S${reset}"
    echo -e "${blue}════════════════════════════════════════════════════════════${reset}"
}

title() {
    echo
    echo -e "${blue}================================================${reset}"
    echo -e "${blue}${bold}$1${reset}"
    echo -e "${blue}================================================${reset}"
    echo
}

step() {
    step_count=$((step_count + 1))
    local why="${2:-}"
    local label="Etape ${step_count}/${TOTAL_STEPS} - $1"
    echo
    echo -e "${blue}${bold}${label}${reset}"
    echo -e "${blue}$(printf -- '─%.0s' $(seq 1 ${#label}))${reset}"
    if [ -n "$why" ]; then
        echo -e "  $why"
    fi
    echo
}

success_line() { echo -e "${green}✓ $1${reset}"; }
warn_line() { echo -e "${yellow}$1${reset}"; }
error_line() { echo -e "${red}$1${reset}"; }

box_start() { echo -e "${blue}╔══════════════════════════════════════════════════════════╗${reset}"; }
box_end() { echo -e "${blue}╚══════════════════════════════════════════════════════════╝${reset}"; }

read_with_countdown() {
    local timeout="$1" varname="$2"
    local input="" ch remaining="$timeout" started=0
    while true; do
        if [ "$started" = 0 ]; then
            printf "\r${blue}${bold}> (%2ds restantes)${reset} " "$remaining"
        else
            printf "\r> %s   " "$input"
        fi
        if IFS= read -r -s -n1 -t 1 ch; then
            if [ -z "$ch" ]; then
                break
            fi
            started=1
            if [ "$ch" = $'\x7f' ] || [ "$ch" = $'\b' ]; then
                input="${input%?}"
            else
                input="${input}${ch}"
            fi
        elif [ "$started" = 0 ]; then
            remaining=$((remaining - 1))
            if [ "$remaining" -le 0 ]; then
                printf "\n"
                printf -v "$varname" '%s' ""
                return 1
            fi
        fi
    done
    printf "\n"
    printf -v "$varname" '%s' "$input"
    return 0
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$script_dir/components"
alert_box_user="cron.alerts"
install_log="/var/log/wappos-install-detail.log"

network_configured_marker="$script_dir/.network-configured"

quiet() {
    "$@" >>"$install_log" 2>&1 &
    local pid=$! spin='-\|/' i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i + 1) % 4 ))
        printf "\r  %s En cours... Patientez !" "${spin:$i:1}"
        sleep 0.2
    done
    wait "$pid"
    local rc=$?
    printf "\r%40s\r" " "
    return $rc
}

banner
echo
echo "Le detail technique de chaque etape est enregistre dans $install_log"

if [ ! -f "$network_configured_marker" ]; then
    step "Configuration reseau" "Verifie comment ce serveur va se connecter a Internet."
    echo "Ce serveur utilise l'adresse IP fournie automatiquement par votre routeur (DHCP)."
    echo "Aucune action requise ici. Une adresse fixe pourra etre proposee a la fin"
    echo "de cette installation, une fois Wappos en place."
    touch "$network_configured_marker"
fi

step "Attente du reseau" "S'assure que la connexion est bien active avant de continuer."
tries=0
until getent hosts install.yunohost.org >/dev/null 2>&1; do
    tries=$((tries + 1))
    if [ "$tries" -ge 30 ]; then
        break
    fi
    sleep 2
done

if ! command -v curl >/dev/null 2>&1 || ! command -v rsync >/dev/null 2>&1; then
    quiet apt-get update
    quiet apt-get install -y curl rsync
fi

if ! command -v yunohost >/dev/null 2>&1; then
    step "Installation du moteur systeme Wappos" "Installe le socle technique sur lequel Wappos s'appuie."
    echo "Cette etape peut durer plusieurs minutes, c'est normal."
    tries=0
    until quiet bash -c "curl https://install.yunohost.org | bash -s -- -a"; do
        tries=$((tries + 1))
        if [ "$tries" -ge 4 ]; then
            error_line "Echec apres plusieurs tentatives, abandon. Dernieres lignes du journal :"
            tail -n 40 "$install_log"
            exit 1
        fi
        warn_line "Echec, nouvelle tentative dans 10 secondes (${tries}/4)..."
        sleep 10
    done
    success_line "Moteur systeme installe"
fi

if [ ! -f /etc/yunohost/installed ]; then
    title "Configuration initiale"
    echo "Les questions suivantes vous demandent :"
    echo
    echo -e "  ${bold}- le nom de domaine${reset} de votre serveur"
    echo -e "  ${bold}- un mot de passe administrateur${reset} (robuste, evitez les mots courants)"
    echo -e "  ${bold}- d'accepter les conditions d'utilisation${reset} du systeme"
    echo
    echo -e "${bold}Attention si ce domaine local (.lan/.local) existe deja ailleurs sur votre"
    echo -e "reseau${reset} (une autre installation, un autre serveur) : la resolution DNS de"
    echo "votre reseau pourrait faire pointer ce nom vers l'autre machine plutot que"
    echo "celle-ci. Choisissez un nom clairement distinct pour une installation de test."
    echo
    until yunohost tools postinstall -u adminynh -F "Administrateur"; do
        echo
        echo -e "${bold}Echec, on recommence ces memes questions.${reset}"
        echo
    done
fi

step "Systeme de base installe et configure" "Le socle technique est pret, la suite installe Wappos par-dessus."

if [ -f /usr/bin/yunoprompt ] && ! grep -q "W A P P O S" /usr/bin/yunoprompt; then
    python3 - <<'PYEOF'
import re
path = "/usr/bin/yunoprompt"
with open(path, encoding="utf-8") as f:
    content = f.read()
bar = "═" * 62
new_logo = f"""LOGO=$(cat << 'EOF'
{bar}
                        W A P P O S
{bar}
EOF
)"""
new_content, n = re.subn(r"LOGO=\$\(cat << 'EOF'.*?\nEOF\n\)", new_logo, content, count=1, flags=re.S)
if n == 1:
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
PYEOF
    quiet systemctl restart yunoprompt.service
fi

if ! command -v docker >/dev/null 2>&1; then
    step "Installation de Docker Engine" "Permet a Wappos de faire tourner des applications supplementaires de facon isolee."
    echo "Cette etape peut durer une a deux minutes, c'est normal."
    quiet bash -c "curl -fsSL https://get.docker.com | sh"
    success_line "Docker installe"
fi

if [ ! -f /etc/systemd/system/docker.service.d/nftables-resync.conf ]; then
    step "Protection Docker contre les rechargements nftables" "Evite un bug connu qui pourrait couper Docker apres un redemarrage reseau."
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
    step "Creation du compte technique d'alertes" "Un compte interne pour les notifications systeme, pas pour vous connecter."
    yunohost user create "$alert_box_user" -F "SYSTEME - NE PAS SUPPRIMER" -d "$main_domain" -p "$(openssl rand -base64 24)"
fi

step "Installation des composants Wappos" "Installe le portail, l'administration et les autres briques propres a Wappos."
for component in wappos_api_ynh wappos_sso_bypass wappos_admin_ynh wappos_portal_ynh prometheus_ynh; do
    echo -n "  Installation de $component... "
    quiet bash "$release_dir/$component/standalone/install.sh"
    success_line "OK"
done

if ! yunohost app list --output-as json | python3 -c "import json,sys; sys.exit(0 if 'rspamd' in [a['id'] for a in json.load(sys.stdin)['apps']] else 1)"; then
    step "Installation de Rspamd (antispam)" "Protege vos boites mail contre le spam."
    quiet yunohost app install rspamd

    cat > /etc/rspamd/local.d/phishing.conf <<'RSPAMD_PHISHING_EOF'
openphish_enabled = true;
RSPAMD_PHISHING_EOF

    rspamd_password="$(openssl rand -base64 24)"
    rspamd_password_hash="$(rspamadm pw -p "$rspamd_password")"
    printf 'password = "%s";\n' "$rspamd_password_hash" > /etc/rspamd/local.d/worker-controller.inc

    quiet rspamadm configtest
    systemctl reload rspamd
    success_line "Rspamd installe"
fi

step "Finalisation de la liaison Prometheus / wappos_admin" "Connecte le tableau de bord de performance a l'administration."
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

step "Connexion SSH par mot de passe"
echo "Par defaut, la connexion root en SSH accepte un mot de passe en plus"
echo "des cles. Pour un serveur expose sur Internet, il est recommande de"
echo "n'accepter que les cles SSH (plus resistant aux attaques par force brute)."
echo
if [ -s /root/.ssh/authorized_keys ]; then
    echo -e "${bold}Une cle SSH est deja enregistree pour root.${reset} Desactiver la connexion"
    echo "par mot de passe maintenant ? [o/N] (20 secondes, sinon N par defaut)"
    read_with_countdown 20 disable_ssh_password || disable_ssh_password="n"

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
echo "maintenant ? [o/N] (20 secondes, sinon N par defaut)"
read_with_countdown 20 set_static_ip || set_static_ip="n"

final_ip="$current_ip"

if [ "$set_static_ip" = "o" ] || [ "$set_static_ip" = "O" ]; then
    echo
    if read -t 60 -rp "Adresse IP fixe (ex. 192.168.1.201) : " static_ip \
        && read -t 60 -rp "Masque de sous-reseau (ex. 255.255.255.0) : " static_netmask \
        && read -t 60 -rp "Passerelle (ex. 192.168.1.254) : " static_gateway \
        && read -t 60 -rp "Serveur DNS (ex. 192.168.1.254) : " static_dns; then

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

        systemctl restart networking
        final_ip="$static_ip"
        echo "Appuyez sur Entree pour continuer..."
        read_with_countdown 20 _ || true
    else
        echo
        echo "Pas de reponse, IP fixe non configuree. Le serveur reste en DHCP."
    fi
fi

echo
box_start
success_line "Wappos est pret"
box_end
echo
echo -e "${bold}L'installation est terminee.${reset} Connectez-vous avec :"
echo
echo -e "  Portail        : ${bold}https://$main_domain/wappos-portal/${reset}  (ou https://$final_ip/wappos-portal/)"
echo -e "  Administration : ${bold}https://$main_domain/wappos-admin/${reset}  (ou https://$final_ip/wappos-admin/)"
echo
echo -e "${blue}${bold}  >>> IDENTIFIANT : adminynh${reset}"
echo -e "${blue}${bold}  >>> MOT DE PASSE : celui que vous venez de definir ci-dessus${reset}"
echo
