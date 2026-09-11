#!/bin/bash
# Auteur : Patrick Ritaine
set -euo pipefail

clear

bold="\033[1m"
underline="\033[4m"
reset="\033[0m"
blue="\033[1;36m"
green="\033[1;32m"
red="\033[1;31m"
yellow="\033[1;33m"

step_count=0

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
    local label
    label="$(t step_label_prefix) ${step_count} - $1"
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
            printf "\r\033[K${blue}${bold}> (%2ds restantes)${reset} " "$remaining"
        else
            printf "\r\033[K> %s" "$input"
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

t() {
    local key="$1"
    if [ "${WAPPOS_LANG:-en}" = "fr" ]; then
        case "$key" in
            step_label_prefix) echo "Etape" ;;
            log_detail_fmt) echo "Le detail technique de chaque etape est enregistre dans %s" ;;
            step_network_title) echo "Configuration reseau" ;;
            step_network_why) echo "Verifie comment ce serveur va se connecter a Internet." ;;
            network_msg1) echo "Ce serveur utilise l'adresse IP fournie automatiquement par votre routeur (DHCP)," ;;
            network_msg2) echo "sauf si une configuration manuelle a ete choisie pendant l'installation Debian qui" ;;
            network_msg3) echo "vient de se terminer. Aucune action requise ici." ;;
            network_msg4) echo "Pour une adresse IP fixe : debranchez le reseau (ou coupez le Wi-Fi) avant de" ;;
            network_msg5) echo "demarrer l'installateur Debian - il proposera alors la configuration manuelle." ;;
            step_wait_network_title) echo "Attente du reseau" ;;
            step_wait_network_why) echo "S'assure que la connexion est bien active avant de continuer." ;;
            step_install_engine_title) echo "Installation du moteur systeme Wappos" ;;
            step_install_engine_why) echo "Installe le socle technique sur lequel Wappos s'appuie." ;;
            install_engine_msg1) echo "Cette etape peut durer plusieurs minutes, c'est normal." ;;
            err_after_retries) echo "Echec apres plusieurs tentatives, abandon. Dernieres lignes du journal :" ;;
            warn_retry_fmt) echo "Echec, nouvelle tentative dans 10 secondes (%s/4)..." ;;
            success_engine_installed) echo "Moteur systeme installe" ;;
            step_gui_title) echo "Interface graphique Wappos" ;;
            step_gui_why) echo "Application et lancement de l'interface graphique pour la configuration initiale." ;;
            success_gui) echo "Interface graphique Wappos appliquee" ;;
            title_finalize_browser) echo "Finalisation via votre navigateur" ;;
            finalize_msg1) echo "La derniere etape (nom de domaine, identifiant, mot de passe) se termine" ;;
            finalize_msg2) echo "depuis un navigateur, exactement comme Wappos vous y invitera." ;;
            finalize_warn1) echo "Attention si ce domaine local (.lan/.local) existe deja ailleurs sur votre" ;;
            finalize_warn2) echo "reseau (une autre installation, un autre serveur) : choisissez un nom" ;;
            finalize_warn3) echo "clairement distinct pour une installation de test." ;;
            finalize_open_browser) echo "Ouvrez un navigateur sur une autre machine du meme reseau et allez sur :" ;;
            finalize_follow1) echo "Suivez les instructions a l'ecran. Cette etape reprend automatiquement" ;;
            finalize_follow2) echo "des que vous avez valide le formulaire, sans rien taper ici." ;;
            finalize_dont_leave1) echo "NE FERMEZ PAS CETTE FENETRE ET NE TOUCHEZ A RIEN ICI." ;;
            finalize_dont_leave2) echo "Remplir le formulaire dans le navigateur ne termine PAS l'installation :" ;;
            finalize_dont_leave3) echo "l'installation continue ensuite ICI, sur cet ecran, automatiquement." ;;
            finalize_waiting) echo "En attente de la finalisation depuis votre navigateur..." ;;
            finalize_done) echo "Configuration initiale terminee" ;;
            step_base_installed_title) echo "Systeme de base installe et configure" ;;
            step_base_installed_why) echo "Le socle technique est pret, la suite installe Wappos par-dessus." ;;
            step_docker_title) echo "Installation de Docker Engine" ;;
            step_docker_why) echo "Permet a Wappos de faire tourner des applications supplementaires de facon isolee." ;;
            docker_msg1) echo "Cette etape peut durer une a deux minutes, c'est normal." ;;
            success_docker) echo "Docker installe" ;;
            step_nftables_title) echo "Protection Docker contre les rechargements nftables" ;;
            step_nftables_why) echo "Evite un bug connu qui pourrait couper Docker apres un redemarrage reseau." ;;
            step_alert_account_title) echo "Creation du compte technique d'alertes" ;;
            step_alert_account_why) echo "Un compte interne pour les notifications systeme, pas pour vous connecter." ;;
            success_alert_account) echo "Compte technique d'alertes cree" ;;
            step_components_title) echo "Installation des composants Wappos" ;;
            step_components_why) echo "Installe le portail, l'administration et les autres briques propres a Wappos." ;;
            installing_component_fmt) echo "  Installation de %s..." ;;
            component_installed_fmt) echo "  %s installe" ;;
            step_rspamd_title) echo "Installation de Rspamd (antispam)" ;;
            step_rspamd_why) echo "Protege vos boites mail contre le spam." ;;
            success_rspamd) echo "Rspamd installe" ;;
            step_prometheus_title) echo "Finalisation de la liaison Prometheus / wappos_admin" ;;
            step_prometheus_why) echo "Connecte le tableau de bord de performance a l'administration." ;;
            success_components) echo "Composants Wappos installes." ;;
            step_ssh_password_title) echo "Connexion SSH par mot de passe" ;;
            ssh_msg1) echo "Par defaut, seules les cles SSH sont acceptees pour la connexion root" ;;
            ssh_msg2) echo "(la connexion par mot de passe reste desactivee depuis le premier" ;;
            ssh_msg3) echo "demarrage, pour ne pas exposer ce serveur avant sa configuration)." ;;
            ssh_key_present1) echo "Une cle SSH est deja enregistree pour root." ;;
            ssh_key_present2) echo "Rien a faire, vous pouvez vous connecter normalement." ;;
            ssh_no_key1) echo "Aucune cle SSH enregistree pour root." ;;
            ssh_no_key2) echo "Activer la connexion par mot de passe le temps d'en ajouter une ? [o/N] (20 secondes, sinon N par defaut)" ;;
            ssh_enabled1) echo "Connexion par mot de passe activee." ;;
            ssh_enabled2) echo "Le mot de passe root est celui que vous venez de choisir pour l'administrateur Wappos ci-dessus." ;;
            ssh_enabled3) echo "Pensez a la desactiver a nouveau une fois votre cle ajoutee." ;;
            final_ready) echo "Wappos est pret" ;;
            final_done) echo "L'installation est terminee." ;;
            final_connect) echo "Connectez-vous avec :" ;;
            final_portal_label) echo "Portail" ;;
            final_admin_label) echo "Administration" ;;
            final_or) echo "ou" ;;
            final_username_label) echo ">>> IDENTIFIANT :" ;;
            final_password_label) echo ">>> MOT DE PASSE : celui que vous venez de definir ci-dessus" ;;
            ssh_disabled_default1) echo "Acces SSH desactive par defaut." ;;
            ssh_disabled_default2) echo "Si vous en avez besoin plus tard, connectez-vous en console (identifiant/mot de passe ci-dessus) puis executez :" ;;
            ssh_disabled_default3) echo "Pensez a la desactiver a nouveau une fois votre cle SSH ajoutee :" ;;
            progress_start) echo "Demarrage..." ;;
            progress_base_update) echo "Mise a jour du systeme de base..." ;;
            progress_deps) echo "Installation des dependances necessaires..." ;;
            progress_prep) echo "Preparation de l'installation..." ;;
            progress_sources) echo "Ajout des sources logicielles..." ;;
            progress_core) echo "Installation du coeur du systeme..." ;;
            progress_slapd) echo "Configuration de l'annuaire utilisateurs..." ;;
            progress_postfix) echo "Configuration du service de messagerie..." ;;
            progress_nginx) echo "Configuration du serveur web..." ;;
            progress_fail2ban) echo "Configuration de la protection contre les intrusions..." ;;
            progress_yunohost) echo "Finalisation de la configuration..." ;;
            spinner_wait) echo "En cours... Patientez !" ;;
            *) echo "$key" ;;
        esac
    else
        case "$key" in
            step_label_prefix) echo "Step" ;;
            log_detail_fmt) echo "Technical detail for each step is logged in %s" ;;
            step_network_title) echo "Network configuration" ;;
            step_network_why) echo "Checks how this server will connect to the Internet." ;;
            network_msg1) echo "This server uses the IP address automatically provided by your router (DHCP)," ;;
            network_msg2) echo "unless manual configuration was chosen during the Debian installation that" ;;
            network_msg3) echo "just finished. No action needed here." ;;
            network_msg4) echo "For a fixed IP address: unplug the network (or turn off Wi-Fi) before" ;;
            network_msg5) echo "starting the Debian installer - it will then offer manual configuration." ;;
            step_wait_network_title) echo "Waiting for network" ;;
            step_wait_network_why) echo "Makes sure the connection is active before continuing." ;;
            step_install_engine_title) echo "Installing the Wappos system engine" ;;
            step_install_engine_why) echo "Installs the technical foundation Wappos relies on." ;;
            install_engine_msg1) echo "This step can take several minutes, that's normal." ;;
            err_after_retries) echo "Failed after several attempts, aborting. Last lines of the log:" ;;
            warn_retry_fmt) echo "Failed, retrying in 10 seconds (%s/4)..." ;;
            success_engine_installed) echo "System engine installed" ;;
            step_gui_title) echo "Wappos graphical interface" ;;
            step_gui_why) echo "Applies and launches the graphical interface for initial setup." ;;
            success_gui) echo "Graphical interface applied" ;;
            title_finalize_browser) echo "Finishing up in your browser" ;;
            finalize_msg1) echo "The last step (domain name, username, password) is completed" ;;
            finalize_msg2) echo "from a browser, exactly as Wappos will invite you to." ;;
            finalize_warn1) echo "Careful if this local domain (.lan/.local) already exists elsewhere on your" ;;
            finalize_warn2) echo "network (another install, another server): choose a clearly distinct name" ;;
            finalize_warn3) echo "for a test installation." ;;
            finalize_open_browser) echo "Open a browser on another machine on the same network and go to:" ;;
            finalize_follow1) echo "Follow the on-screen instructions. This step resumes automatically" ;;
            finalize_follow2) echo "once you've submitted the form, nothing to type here." ;;
            finalize_dont_leave1) echo "DO NOT CLOSE THIS WINDOW AND DO NOT TOUCH ANYTHING HERE." ;;
            finalize_dont_leave2) echo "Submitting the browser form does NOT finish the installation:" ;;
            finalize_dont_leave3) echo "the installation then continues HERE, on this screen, automatically." ;;
            finalize_waiting) echo "Waiting for finalization from your browser..." ;;
            finalize_done) echo "Initial configuration complete" ;;
            step_base_installed_title) echo "Base system installed and configured" ;;
            step_base_installed_why) echo "The technical foundation is ready, Wappos is installed on top next." ;;
            step_docker_title) echo "Installing Docker Engine" ;;
            step_docker_why) echo "Lets Wappos run additional applications in isolation." ;;
            docker_msg1) echo "This step can take one to two minutes, that's normal." ;;
            success_docker) echo "Docker installed" ;;
            step_nftables_title) echo "Protecting Docker from nftables reloads" ;;
            step_nftables_why) echo "Avoids a known bug that could take Docker down after a network restart." ;;
            step_alert_account_title) echo "Creating the technical alert account" ;;
            step_alert_account_why) echo "An internal account for system notifications, not for you to log in with." ;;
            success_alert_account) echo "Technical alert account created" ;;
            step_components_title) echo "Installing Wappos components" ;;
            step_components_why) echo "Installs the portal, administration, and other Wappos-specific building blocks." ;;
            installing_component_fmt) echo "  Installing %s..." ;;
            component_installed_fmt) echo "  %s installed" ;;
            step_rspamd_title) echo "Installing Rspamd (antispam)" ;;
            step_rspamd_why) echo "Protects your mailboxes against spam." ;;
            success_rspamd) echo "Rspamd installed" ;;
            step_prometheus_title) echo "Finalizing the Prometheus / wappos_admin link" ;;
            step_prometheus_why) echo "Connects the performance dashboard to the admin panel." ;;
            success_components) echo "Wappos components installed." ;;
            step_ssh_password_title) echo "SSH password login" ;;
            ssh_msg1) echo "By default, only SSH keys are accepted for root login" ;;
            ssh_msg2) echo "(password login stays disabled from first boot, so this server" ;;
            ssh_msg3) echo "isn't exposed before it's configured)." ;;
            ssh_key_present1) echo "An SSH key is already registered for root." ;;
            ssh_key_present2) echo "Nothing to do, you can log in normally." ;;
            ssh_no_key1) echo "No SSH key registered for root." ;;
            ssh_no_key2) echo "Enable password login long enough to add one? [y/N] (20 seconds, N by default)" ;;
            ssh_enabled1) echo "Password login enabled." ;;
            ssh_enabled2) echo "The root password is the one you just chose for the Wappos administrator above." ;;
            ssh_enabled3) echo "Remember to disable it again once your key has been added." ;;
            final_ready) echo "Wappos is ready" ;;
            final_done) echo "Installation complete." ;;
            final_connect) echo "Log in with:" ;;
            final_portal_label) echo "Portal" ;;
            final_admin_label) echo "Administration" ;;
            final_or) echo "or" ;;
            final_username_label) echo ">>> USERNAME:" ;;
            final_password_label) echo ">>> PASSWORD: the one you just set above" ;;
            ssh_disabled_default1) echo "SSH access disabled by default." ;;
            ssh_disabled_default2) echo "If you need it later, log in via console (username/password above) then run:" ;;
            ssh_disabled_default3) echo "Remember to disable it again once your SSH key has been added:" ;;
            progress_start) echo "Starting..." ;;
            progress_base_update) echo "Updating the base system..." ;;
            progress_deps) echo "Installing required dependencies..." ;;
            progress_prep) echo "Preparing the installation..." ;;
            progress_sources) echo "Adding software sources..." ;;
            progress_core) echo "Installing the system core..." ;;
            progress_slapd) echo "Configuring the user directory..." ;;
            progress_postfix) echo "Configuring the mail service..." ;;
            progress_nginx) echo "Configuring the web server..." ;;
            progress_fail2ban) echo "Configuring intrusion protection..." ;;
            progress_yunohost) echo "Finalizing configuration..." ;;
            spinner_wait) echo "Working... please wait!" ;;
            *) echo "$key" ;;
        esac
    fi
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
release_dir="$script_dir/components"
alert_box_user="cron.alerts"
install_log="/var/log/wappos-install-detail.log"

network_configured_marker="$script_dir/.network-configured"
wappos_lang_file="/etc/wappos/language"

if [ -f "$wappos_lang_file" ]; then
    WAPPOS_LANG="$(cat "$wappos_lang_file")"
else
    clear
    echo
    box_start
    echo -e "${blue}${bold}${underline}  Language / Langue :${reset}"
    echo
    echo -e "  ${bold}[1] English (default)${reset}"
    echo -e "  ${bold}[2] Francais${reset}"
    box_end
    echo
    read_with_countdown 45 lang_choice || lang_choice=""
    case "$lang_choice" in
        2|f|F) WAPPOS_LANG="fr" ;;
        *) WAPPOS_LANG="en" ;;
    esac
    mkdir -p "$(dirname "$wappos_lang_file")"
    printf '%s' "$WAPPOS_LANG" > "$wappos_lang_file"
fi

quiet() {
    "$@" >>"$install_log" 2>&1 &
    local pid=$! spin='-\|/' i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i + 1) % 4 ))
        printf "\r  %s %s" "${spin:$i:1}" "$(t spinner_wait)"
        sleep 0.2
    done
    wait "$pid"
    local rc=$?
    printf "\r%40s\r" " "
    return $rc
}

quiet_with_progress() {
    local seen_line=0 phase
    phase="$(t progress_start)"
    "$@" >>"$install_log" 2>&1 &
    local pid=$! spin='-\|/' i=0
    while kill -0 "$pid" 2>/dev/null; do
        i=$(( (i + 1) % 4 ))
        local total_lines
        total_lines=$(wc -l < "$install_log" 2>/dev/null || echo 0)
        if [ "$total_lines" -gt "$seen_line" ]; then
            local new_content
            new_content="$(tail -n "+$((seen_line + 1))" "$install_log" 2>/dev/null)"
            seen_line=$total_lines
            if echo "$new_content" | grep -q "1/5"; then
                phase="$(t progress_base_update)"
            elif echo "$new_content" | grep -q "2/5"; then
                phase="$(t progress_deps)"
            elif echo "$new_content" | grep -q "3/5"; then
                phase="$(t progress_prep)"
            elif echo "$new_content" | grep -q "4/5"; then
                phase="$(t progress_sources)"
            elif echo "$new_content" | grep -q "5/5"; then
                phase="$(t progress_core)"
            elif echo "$new_content" | grep -q "Setting up slapd ("; then
                phase="$(t progress_slapd)"
            elif echo "$new_content" | grep -q "Setting up postfix ("; then
                phase="$(t progress_postfix)"
            elif echo "$new_content" | grep -q "Setting up nginx"; then
                phase="$(t progress_nginx)"
            elif echo "$new_content" | grep -q "Setting up fail2ban ("; then
                phase="$(t progress_fail2ban)"
            elif echo "$new_content" | grep -q "Setting up yunohost ("; then
                phase="$(t progress_yunohost)"
            fi
        fi
        printf "\r\033[K  %s %s" "${spin:$i:1}" "$phase"
        sleep 0.3
    done
    wait "$pid"
    local rc=$?
    printf "\r\033[K"
    return $rc
}

banner
echo
printf "$(t log_detail_fmt)\n" "$install_log"

if [ ! -f "$network_configured_marker" ]; then
    step "$(t step_network_title)" "$(t step_network_why)"
    echo "$(t network_msg1)"
    echo "$(t network_msg2)"
    echo "$(t network_msg3)"
    echo
    echo "$(t network_msg4)"
    echo "$(t network_msg5)"
    touch "$network_configured_marker"
fi

step "$(t step_wait_network_title)" "$(t step_wait_network_why)"
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
    step "$(t step_install_engine_title)" "$(t step_install_engine_why)"
    echo "$(t install_engine_msg1)"
    tries=0
    until quiet_with_progress bash -c "curl --ipv4 https://install.yunohost.org | bash -s -- -a"; do
        tries=$((tries + 1))
        if [ "$tries" -ge 4 ]; then
            error_line "$(t err_after_retries)"
            tail -n 40 "$install_log"
            exit 1
        fi
        warn_line "$(printf "$(t warn_retry_fmt)" "$tries")"
        sleep 10
    done
    echo
    success_line "$(t success_engine_installed)"
fi

if [ ! -f /etc/yunohost/installed ] && ! systemctl list-unit-files wappos_postinstall.service >/dev/null 2>&1; then
    step "$(t step_gui_title)" "$(t step_gui_why)"
    quiet bash "$release_dir/wappos_postinstall/standalone/install.sh"
    success_line "$(t success_gui)"
fi

if [ ! -f /etc/yunohost/installed ]; then
    title "$(t title_finalize_browser)"
    echo "$(t finalize_msg1)"
    echo "$(t finalize_msg2)"
    echo
    echo -e "${bold}$(t finalize_warn1)"
    echo -e "$(t finalize_warn2)${reset} $(t finalize_warn3)"
    echo

    interface="$(ip route show default | awk '{print $5; exit}')"
    current_ip="$(ip -4 -o addr show dev "$interface" | awk '{print $4}' | cut -d/ -f1 | head -n1)"
    echo -e "${bold}$(t finalize_open_browser)${reset}"
    echo
    echo -e "  ${blue}${bold}https://${current_ip}/${reset}"
    echo
    echo "$(t finalize_follow1)"
    echo "$(t finalize_follow2)"
    echo
    echo -e "${red}${bold}╔══════════════════════════════════════════════════════════╗${reset}"
    echo -e "${red}${bold}  $(t finalize_dont_leave1)${reset}"
    echo -e "${red}  $(t finalize_dont_leave2)${reset}"
    echo -e "${red}  $(t finalize_dont_leave3)${reset}"
    echo -e "${red}${bold}╚══════════════════════════════════════════════════════════╝${reset}"
    echo

    i=0
    spin='-\|/'
    until [ -f /etc/yunohost/installed ]; do
        i=$(( (i + 1) % 4 ))
        printf "\r  %s %s" "${spin:$i:1}" "$(t finalize_waiting)"
        sleep 2
    done
    printf "\r%70s\r" " "
    success_line "$(t finalize_done)"
fi

step "$(t step_base_installed_title)" "$(t step_base_installed_why)"

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
    step "$(t step_docker_title)" "$(t step_docker_why)"
    echo "$(t docker_msg1)"
    tries=0
    until quiet bash -c "curl --ipv4 -fsSL https://get.docker.com | sh"; do
        tries=$((tries + 1))
        if [ "$tries" -ge 4 ]; then
            error_line "$(t err_after_retries)"
            tail -n 40 "$install_log"
            exit 1
        fi
        warn_line "$(printf "$(t warn_retry_fmt)" "$tries")"
        sleep 10
    done
    success_line "$(t success_docker)"
fi

if [ ! -f /etc/systemd/system/docker.service.d/nftables-resync.conf ]; then
    step "$(t step_nftables_title)" "$(t step_nftables_why)"
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
admin_username="$(yunohost user list --output-as json | python3 -c "import json,sys; users=json.load(sys.stdin)['users']; print(next(iter(users), 'wappos_admin'))")"

if ! yunohost user list --output-as json | python3 -c "import json,sys; sys.exit(0 if '$alert_box_user' in json.load(sys.stdin)['users'] else 1)"; then
    step "$(t step_alert_account_title)" "$(t step_alert_account_why)"
    quiet yunohost user create "$alert_box_user" -F "SYSTEME - NE PAS SUPPRIMER" -d "$main_domain" -p "$(openssl rand -base64 24)"
    success_line "$(t success_alert_account)"
fi

step "$(t step_components_title)" "$(t step_components_why)"
for component in wappos_api_ynh wappos_sso_bypass wappos_admin_ynh wappos_portal_ynh prometheus_ynh; do
    printf "$(t installing_component_fmt)\n" "$component"
    quiet bash "$release_dir/$component/standalone/install.sh"
    success_line "$(printf "$(t component_installed_fmt)" "$component")"
    echo
done

if ! yunohost app list --output-as json | python3 -c "import json,sys; sys.exit(0 if 'rspamd' in [a['id'] for a in json.load(sys.stdin)['apps']] else 1)"; then
    step "$(t step_rspamd_title)" "$(t step_rspamd_why)"
    quiet yunohost app install rspamd

    cat > /etc/rspamd/local.d/phishing.conf <<'RSPAMD_PHISHING_EOF'
openphish_enabled = true;
RSPAMD_PHISHING_EOF

    rspamd_password="$(openssl rand -base64 24)"
    rspamd_password_hash="$(rspamadm pw -p "$rspamd_password")"
    printf 'password = "%s";\nsecure_ip = "127.0.0.1";\n' "$rspamd_password_hash" > /etc/rspamd/local.d/worker-controller.inc
    install -m 600 /dev/null /root/.wappos-rspamd-password
    printf '%s' "$rspamd_password" > /root/.wappos-rspamd-password

    quiet rspamadm configtest
    systemctl reload rspamd

    bash "$script_dir/branding/rspamd/apply-branding.sh"
    cat > /etc/cron.d/wappos-rspamd-branding <<CRON_EOF
@daily root bash $script_dir/branding/rspamd/apply-branding.sh >/dev/null 2>&1
CRON_EOF

    yunohost app setting rspamd domain -v "$main_domain"
    yunohost app setting rspamd path -v /rspamd
    python3 -c "from yunohost.permission import permission_url; permission_url('rspamd.main', url='/', sync_perm=True)" 2>/dev/null || true
    quiet yunohost app ssowatconf

    mkdir -p "/etc/nginx/conf.d/$main_domain.d"
    cp "$script_dir/branding/rspamd/nginx-rspamd.conf.template" "/etc/nginx/conf.d/$main_domain.d/rspamd.conf"
    nginx -t && systemctl reload nginx

    current_milters="$(postconf -h smtpd_milters)"
    if ! echo "$current_milters" | grep -q "11332"; then
        postconf -e "smtpd_milters = ${current_milters:+$current_milters }inet:localhost:11332"
        systemctl reload postfix
    fi

    success_line "$(t success_rspamd)"
fi

step "$(t step_prometheus_title)" "$(t step_prometheus_why)"
(
    source "$release_dir/wappos_admin_ynh/standalone/vars.sh"
    deploy_prometheus_readonly_user
)
systemctl restart wappos_admin

success_line "$(t success_components)"

interface="$(ip route show default | awk '{print $5; exit}')"
final_ip="$(ip -4 -o addr show dev "$interface" | awk '{print $4}' | cut -d/ -f1 | head -n1)"

security_configured_marker="$script_dir/.security-configured"

if [ ! -f "$security_configured_marker" ]; then
    step "$(t step_ssh_password_title)"
    echo "$(t ssh_msg1)"
    echo "$(t ssh_msg2)"
    echo "$(t ssh_msg3)"
    echo
    if [ -s /root/.ssh/authorized_keys ]; then
        echo -e "${bold}$(t ssh_key_present1)${reset} $(t ssh_key_present2)"
    else
        echo -e "${bold}$(t ssh_no_key1)${reset}"
        echo "$(t ssh_no_key2)"
        read_with_countdown 20 enable_ssh_password || enable_ssh_password="n"

        case "$enable_ssh_password" in
            y|Y|o|O)
                cp /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak-$(date +%Y%m%d)"
                sed -i 's/^#\?PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
                sshd -t
                systemctl reload sshd
                echo -e "${bold}$(t ssh_enabled1)${reset} $(t ssh_enabled2)"
                echo "$(t ssh_enabled3)"
                ;;
        esac
    fi
    echo

    touch "$security_configured_marker"
fi

portal_label="$(t final_portal_label)"
admin_label="$(t final_admin_label)"
label_width=${#admin_label}
[ ${#portal_label} -gt "$label_width" ] && label_width=${#portal_label}

echo
box_start
success_line "$(t final_ready)"
box_end
echo
echo -e "${bold}$(t final_done)${reset} $(t final_connect)"
echo
printf "  %-${label_width}s : ${bold}https://%s/wappos-portal/${reset}  (%s https://%s/wappos-portal/)\n" "$portal_label" "$main_domain" "$(t final_or)" "$final_ip"
printf "  %-${label_width}s : ${bold}https://%s/wappos-admin/${reset}  (%s https://%s/wappos-admin/)\n" "$admin_label" "$main_domain" "$(t final_or)" "$final_ip"
echo
echo -e "${blue}${bold}  $(t final_username_label) ${admin_username}${reset}"
echo -e "${blue}${bold}  $(t final_password_label)${reset}"
echo

if grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config 2>/dev/null; then
    echo -e "${bold}$(t ssh_disabled_default1)${reset} $(t ssh_disabled_default2)"
    echo
    echo -e "  ${bold}sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && systemctl reload ssh${reset}"
    echo
    echo "$(t ssh_disabled_default3)"
    echo -e "  ${bold}sed -i 's/^PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && systemctl reload ssh${reset}"
    echo
fi

if [ -f /usr/bin/yunoprompt ] && ! grep -q "Wappos Portal\|Portail Wappos" /usr/bin/yunoprompt; then
    export WAPPOS_DOMAIN="$main_domain"
    export WAPPOS_IP="$final_ip"
    export WAPPOS_USERNAME="$admin_username"
    export WAPPOS_SSH_DISABLED="$(grep -q "^PasswordAuthentication no" /etc/ssh/sshd_config 2>/dev/null && echo 1 || echo 0)"
    export WAPPOS_LANG
    python3 - <<'PYEOF'
import os
import re
path = "/usr/bin/yunoprompt"
domain = os.environ["WAPPOS_DOMAIN"]
ip = os.environ["WAPPOS_IP"]
username = os.environ["WAPPOS_USERNAME"]
ssh_disabled = os.environ["WAPPOS_SSH_DISABLED"] == "1"
lang = os.environ.get("WAPPOS_LANG", "en")
with open(path, encoding="utf-8") as f:
    content = f.read()

noise_pattern = re.compile(
    r" Local SSL CA X509 fingerprint:\n.*?\$\{fingerprint\[2\]\}\n",
    re.S,
)
content = noise_pattern.sub("", content, count=1)

if lang == "fr":
    portal_label = "Portail Wappos"
    admin_label = "Administration Wappos"
    username_label = "Identifiant"
    ssh_disabled_label = "Acces SSH desactive - pour l'activer, executez :"
else:
    portal_label = "Wappos Portal"
    admin_label = "Wappos Administration"
    username_label = "Username"
    ssh_disabled_label = "SSH access disabled - to enable it, run:"

anchor = "Local IP: ${local_ip:-(no ip detected?)}"
label_width = max(len(portal_label), len(admin_label), len(username_label))
block = (
    "\n"
    f" {portal_label.ljust(label_width)} : https://{domain}/wappos-portal/ ({'ou' if lang == 'fr' else 'or'} https://{ip}/wappos-portal/)\n"
    f" {admin_label.ljust(label_width)} : https://{domain}/wappos-admin/ ({'ou' if lang == 'fr' else 'or'} https://{ip}/wappos-admin/)\n"
    f" {username_label.ljust(label_width)} : {username}"
)
if ssh_disabled:
    block += (
        "\n\n"
        f" {ssh_disabled_label}\n"
        " sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config && systemctl reload ssh"
    )
if anchor in content:
    content = content.replace(anchor, anchor + block, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
PYEOF
    systemctl restart yunoprompt.service
fi
