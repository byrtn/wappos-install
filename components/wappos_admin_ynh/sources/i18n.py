# Auteur : Patrick Ritaine

DEFAULT_LANG = "en"
LANGS = ("fr", "en")

STRINGS = {
    "nav_logout": {"fr": "Déconnexion", "en": "Log out"},
    "nav_home": {"fr": "Accueil", "en": "Home"},
    "nav_documentation": {"fr": "Documentation", "en": "Documentation"},
    "aria_breadcrumb": {"fr": "Fil d'Ariane", "en": "Breadcrumb"},
    "aria_language_switch": {"fr": "Changer de langue", "en": "Switch language"},
    "aria_close": {"fr": "Fermer", "en": "Close"},
    "header_subtitle_administration": {"fr": "Administration", "en": "Administration"},
    "processing": {"fr": "Traitement en cours…", "en": "Processing…"},
    "toggle_password_show": {"fr": "Afficher", "en": "Show"},
    "toggle_password_hide": {"fr": "Masquer", "en": "Hide"},
    "aria_show_password": {"fr": "Afficher le mot de passe", "en": "Show password"},
    "aria_hide_password": {"fr": "Masquer le mot de passe", "en": "Hide password"},
    "file_remove_cancel": {"fr": "Annuler la suppression", "en": "Cancel removal"},
    "file_remove_confirm": {"fr": "Supprimer", "en": "Remove"},

    "title_login": {"fr": "Connexion", "en": "Log in"},
    "username_label": {"fr": "Identifiant", "en": "Username"},
    "username_placeholder": {"fr": "Nom du compte", "en": "Account name"},
    "password_label": {"fr": "Mot de passe", "en": "Password"},
    "password_placeholder": {"fr": "Mot de passe", "en": "Password"},
    "btn_login": {"fr": "Connexion", "en": "Log in"},
    "err_invalid_credentials": {"fr": "Identifiant ou mot de passe incorrect.", "en": "Incorrect username or password."},
    "err_server_unreachable": {"fr": "Serveur injoignable, réessayez.", "en": "Server unreachable, please try again."},

    "err_passwords_mismatch": {"fr": "Les mots de passe ne correspondent pas.", "en": "Passwords do not match."},
    "msg_root_password_changed": {"fr": "Mot de passe root changé.", "en": "Root password changed."},
    "confirm_word_reboot": {"fr": "REDEMARRER", "en": "RESTART"},
    "confirm_word_shutdown": {"fr": "ETEINDRE", "en": "SHUTDOWN"},
    "confirm_word_upgrade": {"fr": "CONFIRMER", "en": "CONFIRM"},
    "err_confirm_reboot_word": {
        "fr": "Pour redémarrer le serveur, tape exactement {word} dans le champ prévu.",
        "en": "To reboot the server, type exactly {word} in the field provided.",
    },
    "err_confirm_shutdown_word": {
        "fr": "Pour éteindre le serveur, tape exactement {word} dans le champ prévu.",
        "en": "To shut down the server, type exactly {word} in the field provided.",
    },
    "msg_reboot_in_progress_disconnected": {
        "fr": "Redémarrage du serveur en cours (la connexion a été coupée pendant l'opération, ce qui est normal).",
        "en": "Server reboot in progress (the connection was interrupted during the operation, which is normal).",
    },
    "msg_reboot_in_progress": {"fr": "Redémarrage du serveur en cours.", "en": "Server reboot in progress."},
    "msg_shutdown_in_progress_disconnected": {
        "fr": "Extinction du serveur en cours (la connexion a été coupée pendant l'opération, ce qui est normal).",
        "en": "Server shutdown in progress (the connection was interrupted during the operation, which is normal).",
    },
    "msg_shutdown_in_progress": {"fr": "Extinction du serveur en cours.", "en": "Server shutdown in progress."},

    "title_system": {"fr": "Système", "en": "System"},
    "title_security": {"fr": "Sécurité", "en": "Security"},
    "breadcrumb_security": {"fr": "Sécurité", "en": "Security"},
    "h3_ssh_access": {"fr": "Connexion SSH par mot de passe (root)", "en": "SSH password login (root)"},
    "ssh_access_explain": {
        "fr": "Par défaut, seules les clés SSH sont acceptées pour la connexion root — c'est plus sûr. N'activez la connexion par mot de passe que temporairement, le temps d'ajouter une clé, puis désactivez-la à nouveau.",
        "en": "By default, only SSH keys are accepted for root login — this is safer. Only enable password login temporarily, long enough to add a key, then disable it again.",
    },
    "ssh_access_status_enabled": {"fr": "Activée actuellement.", "en": "Currently enabled."},
    "ssh_access_status_disabled": {"fr": "Désactivée actuellement.", "en": "Currently disabled."},
    "btn_ssh_access_enable": {"fr": "Activer temporairement", "en": "Enable temporarily"},
    "btn_ssh_access_disable": {"fr": "Désactiver", "en": "Disable"},
    "confirm_ssh_access_enable": {
        "fr": "Activer la connexion SSH par mot de passe pour root ? N'oubliez pas de la désactiver une fois votre clé SSH ajoutée.",
        "en": "Enable SSH password login for root? Remember to disable it again once your SSH key has been added.",
    },
    "msg_ssh_access_enabled": {"fr": "Connexion par mot de passe activée.", "en": "Password login enabled."},
    "msg_ssh_access_disabled": {"fr": "Connexion par mot de passe désactivée.", "en": "Password login disabled."},
    "h3_root_password_age": {"fr": "Mot de passe root", "en": "Root password"},
    "root_password_changed_on": {
        "fr": "Dernière modification : {when}",
        "en": "Last changed: {when}",
    },
    "root_password_changed_unknown": {
        "fr": "Date de dernière modification inconnue.",
        "en": "Last changed date unknown.",
    },
    "h3_fail2ban": {"fr": "Protection contre les tentatives de connexion (fail2ban)", "en": "Login attempt protection (fail2ban)"},
    "fail2ban_unavailable": {"fr": "fail2ban n'est pas disponible sur ce serveur.", "en": "fail2ban is not available on this server."},
    "fail2ban_total_banned": {
        "fr": "{n} IP{s} actuellement bannie{s}",
        "en": "{n} IP{s} currently banned",
    },
    "th_fail2ban_jail": {"fr": "Service protégé", "en": "Protected service"},
    "th_fail2ban_banned_ips": {"fr": "Adresses bannies", "en": "Banned addresses"},
    "h3_root_ssh_keys": {"fr": "Clés SSH autorisées (root)", "en": "Authorized SSH keys (root)"},
    "root_ssh_keys_explain": {
        "fr": "Ces clés peuvent se connecter en SSH en tant que root, même quand la connexion par mot de passe est désactivée. Liste en lecture seule.",
        "en": "These keys can log in via SSH as root, even while password login is disabled. Read-only list.",
    },
    "no_root_ssh_key": {"fr": "Aucune clé SSH enregistrée pour root.", "en": "No SSH key registered for root."},
    "th_key_type": {"fr": "Type", "en": "Type"},
    "th_fingerprint": {"fr": "Empreinte", "en": "Fingerprint"},
    "h3_diagnosis_shortcut": {"fr": "Diagnostic de sécurité", "en": "Security diagnosis"},
    "diagnosis_shortcut_explain": {
        "fr": "Ports ouverts, certificats, mises à jour de sécurité en attente : le diagnostic complet de l'installation se trouve dans Diagnostic.",
        "en": "Open ports, certificates, pending security updates: the full installation diagnosis is available on the Diagnosis page.",
    },
    "btn_go_to_diagnosis": {"fr": "Aller au diagnostic", "en": "Go to diagnosis"},
    "breadcrumb_updates": {"fr": "Mises à jour", "en": "Updates"},
    "banner_api_restarting": {
        "fr": "L'API Wappos redémarre suite à la mise à jour — rafraîchissement automatique dans {countdown}s.",
        "en": "The Wappos API is restarting after the update — automatic refresh in {countdown}s.",
    },
    "banner_reboot_required_prefix": {
        "fr": "Le serveur a installé une mise à jour (noyau ou composant système critique) qui nécessite un redémarrage pour être pleinement active. Le noyau actuellement chargé est ",
        "en": "The server installed an update (kernel or critical system component) that requires a reboot to be fully active. The kernel currently loaded is ",
    },
    "banner_reboot_required_suffix": {
        "fr": ", potentiellement différent de celui installé sur disque.",
        "en": ", potentially different from the one installed on disk.",
    },
    "h3_system_status": {"fr": "État du système", "en": "System status"},
    "label_host": {"fr": "Hôte", "en": "Host"},
    "label_os": {"fr": "Système", "en": "OS"},
    "label_kernel": {"fr": "Noyau", "en": "Kernel"},
    "label_uptime": {"fr": "En ligne depuis", "en": "Uptime"},
    "label_load": {"fr": "Charge (1/5/15 min)", "en": "Load (1/5/15 min)"},
    "word_core": {"fr": "cœur", "en": "core"},
    "label_memory": {"fr": "Mémoire", "en": "Memory"},
    "used_of_total": {
        "fr": "{used} utilisés sur {total} ({percent}%)",
        "en": "{used} used out of {total} ({percent}%)",
    },
    "label_swap": {"fr": "Swap", "en": "Swap"},
    "no_swap_configured": {"fr": "Aucun swap configuré.", "en": "No swap configured."},
    "h3_versions": {"fr": "Versions", "en": "Versions"},
    "no_version_info": {"fr": "Aucune information de version disponible.", "en": "No version information available."},
    "h3_updates_available": {"fr": "Mises à jour disponibles", "en": "Updates available"},
    "label_apps": {"fr": "Apps", "en": "Apps"},
    "word_confirmed": {"fr": "confirmée(s)", "en": "confirmed"},
    "to_check_unknown_target": {
        "fr": ", {n} à vérifier (version cible inconnue — voir liste ci-dessous)",
        "en": ", {n} to check (unknown target version — see list below)",
    },
    "count_available": {"fr": "{n} disponible(s)", "en": "{n} available"},
    "btn_refresh_list": {"fr": "Rafraîchir la liste", "en": "Refresh list"},
    "packages_checked_ago": {"fr": "Paquets système vérifiés il y a {h} h", "en": "System packages checked {h}h ago"},
    "catalog_checked_ago": {"fr": "catalogue d'apps vérifié il y a {h} h", "en": "app catalog checked {h}h ago"},
    "too_old_refresh": {
        "fr": "— trop ancien, rafraîchissez la liste pour voir le détail des mises à jour.",
        "en": "— too old, refresh the list to see update details.",
    },
    "major_upgrade_detected": {
        "fr": "Mise à jour majeure de Wappos détectée — peut redémarrer l'API en cours de route (voir note ci-dessous) et modifier significativement le comportement du serveur. Lisez les notes de version avant de continuer.",
        "en": "Major Wappos update detected — may restart the API mid-process (see note below) and significantly change server behavior. Read the release notes before continuing.",
    },
    "pending_migrations_prefix": {
        "fr": "{n} migration(s) système en attente. Certaines s'exécutent automatiquement lors de la mise à jour du système ; les migrations marquées comme manuelles (montées de version majeures notamment) ne le sont pas et doivent être lancées explicitement — voir la page ",
        "en": "{n} pending system migration(s). Some run automatically during the system update; migrations marked as manual (major version upgrades in particular) do not and must be triggered explicitly — see the ",
    },
    "nav_migrations": {"fr": "Migrations", "en": "Migrations"},
    "h4_applications": {"fr": "Applications", "en": "Applications"},
    "missing_requirements_note": {
        "fr": "(prérequis non satisfaits — nécessite « forcer » sur sa fiche)",
        "en": "(requirements not met — needs \"force\" on its page)",
    },
    "version_from_to": {"fr": "de {cur} à {new}", "en": "from {cur} to {new}"},
    "currently_on_unknown_target": {
        "fr": "actuellement en {cur} — à vérifier, version cible inconnue",
        "en": "currently on {cur} — to check, unknown target version",
    },
    "note_force_excluded": {
        "fr": "Le bouton « Lancer la mise à jour » (Apps) ci-dessous n'inclut PAS les apps aux prérequis non satisfaits — mettez-les à jour individuellement depuis leur fiche (« forcer »).",
        "en": "The \"Start update\" button (Apps) below does NOT include apps with unmet requirements — update them individually from their page (\"force\").",
    },
    "h4_system_categories": {"fr": "Système ({n} catégorie(s))", "en": "System ({n} categories)"},
    "word_package": {"fr": "paquet", "en": "package"},
    "confirm_run_upgrade_dialog": {
        "fr": "Lancer la mise à jour ? Cette action peut interrompre temporairement des services.",
        "en": "Start the update? This action may temporarily interrupt services.",
    },
    "alert_type_word_upgrade": {
        "fr": "Pour lancer la mise à jour, tape exactement {word} dans le champ prévu.",
        "en": "To start the update, type exactly {word} in the field provided.",
    },
    "radio_applications": {"fr": "Applications", "en": "Applications"},
    "radio_system_packages": {"fr": "Système (paquets)", "en": "System (packages)"},
    "type_word_to_confirm_upgrade": {
        "fr": "Tapez « {word} » pour lancer la mise à jour",
        "en": "Type \"{word}\" to start the update",
    },
    "btn_start_upgrade": {"fr": "Lancer la mise à jour", "en": "Start update"},
    "h3_regen_conf": {"fr": "Régénérer la configuration", "en": "Regenerate configuration"},
    "regen_conf_desc": {
        "fr": "Régénère les fichiers de configuration système gérés par Wappos (nginx, ssh, etc.).",
        "en": "Regenerates the system configuration files managed by Wappos (nginx, ssh, etc.).",
    },
    "checkbox_preview_only": {"fr": "Aperçu seulement (ne rien appliquer)", "en": "Preview only (apply nothing)"},
    "btn_execute": {"fr": "Exécuter", "en": "Execute"},
    "regen_force_note": {
        "fr": "L'option « forcer » n'est volontairement pas proposée ici : elle écraserait des fichiers nginx personnalisés par Wappos (redirection du portail, restriction d'accès à l'API portail), avec pour effet une régression de sécurité et de fonctionnement silencieuse.",
        "en": "The \"force\" option is deliberately not offered here: it would overwrite nginx files customized by Wappos (portal redirection, portal API access restriction), causing a silent security and functional regression.",
    },
    "no_diff": {"fr": "Aucune différence.", "en": "No difference."},
    "h3_root_password": {"fr": "Mot de passe root", "en": "Root password"},
    "new_root_password_label": {"fr": "Nouveau mot de passe root", "en": "New root password"},
    "confirm_label": {"fr": "Confirmer", "en": "Confirm"},
    "root_password_requirements": {
        "fr": "8 caractères minimum. Robustesse exacte requise selon le réglage du serveur (profil \"admin\").",
        "en": "8 characters minimum. Exact strength required depends on the server's setting (\"admin\" profile).",
    },
    "btn_change_root_password": {"fr": "Changer le mot de passe root", "en": "Change root password"},
    "h3_danger_zone": {"fr": "Zone dangereuse", "en": "Danger zone"},
    "confirm_reboot_dialog": {
        "fr": "Redémarrer le serveur maintenant ? Tous les services seront interrompus quelques instants.",
        "en": "Reboot the server now? All services will be interrupted for a moment.",
    },
    "type_word_to_confirm_reboot": {
        "fr": "Tapez « {word} » pour confirmer le redémarrage du serveur",
        "en": "Type \"{word}\" to confirm the server reboot",
    },
    "btn_reboot": {"fr": "Redémarrer", "en": "Reboot"},
    "confirm_shutdown_dialog": {
        "fr": "Éteindre le serveur maintenant ? Il faudra un accès physique/console pour le rallumer.",
        "en": "Shut down the server now? You will need physical/console access to turn it back on.",
    },
    "type_word_to_confirm_shutdown": {
        "fr": "Tapez « {word} » pour confirmer l'arrêt du serveur",
        "en": "Type \"{word}\" to confirm the server shutdown",
    },
    "btn_shutdown": {"fr": "Éteindre", "en": "Shut down"},

    "nav_domains": {"fr": "Domaines", "en": "Domains"},
    "word_domain_fallback": {"fr": "Domaine", "en": "Domain"},
    "badge_main_domain": {"fr": "Domaine principal", "en": "Main domain"},
    "confirm_set_main_domain": {"fr": "Faire de {domain} le nouveau domaine principal ?", "en": "Make {domain} the new main domain?"},
    "btn_set_main_domain": {"fr": "Définir comme domaine principal", "en": "Set as main domain"},
    "ca_type_selfsigned": {"fr": "Auto-signé", "en": "Self-signed"},
    "ca_type_other": {"fr": "Autre/Inconnu", "en": "Other/Unknown"},
    "label_certificate": {"fr": "Certificat :", "en": "Certificate:"},
    "valid_for_days": {"fr": "(valide {n} jours)", "en": "(valid for {n} days)"},
    "registrar_via_parent": {"fr": "Registrar : configuré via le domaine parent", "en": "Registrar: configured via the parent domain"},
    "registrar_value": {"fr": "Registrar : {registrar}", "en": "Registrar: {registrar}"},
    "no_app_on_domain": {"fr": "Aucune app sur ce domaine.", "en": "No app on this domain."},
    "h3_operations": {"fr": "Opérations", "en": "Operations"},
    "value_unknown": {"fr": "Inconnu", "en": "Unknown"},
    "value_yes": {"fr": "Oui", "en": "Yes"},
    "value_no": {"fr": "Non", "en": "No"},
    "confirm_cert_not_eligible": {
        "fr": "Ce domaine ne semble pas éligible à un certificat Let's Encrypt (DNS non propagé ?). Continuer quand même ?",
        "en": "This domain doesn't seem eligible for a Let's Encrypt certificate (DNS not propagated?). Continue anyway?",
    },
    "checkbox_force_replace_cert": {"fr": "Forcer (remplacer un certificat déjà valide)", "en": "Force (replace an already valid certificate)"},
    "checkbox_self_signed_cert": {"fr": "Certificat auto-signé (au lieu de Let's Encrypt)", "en": "Self-signed certificate (instead of Let's Encrypt)"},
    "checkbox_no_checks": {"fr": "Ne pas vérifier la config DNS/joignabilité avant (déconseillé)", "en": "Skip DNS/reachability checks beforehand (not recommended)"},
    "btn_install_cert": {"fr": "Installer un certificat Let's Encrypt", "en": "Install a Let's Encrypt certificate"},
    "checkbox_force_ignore_threshold": {"fr": "Forcer (ignorer le seuil de 15 jours)", "en": "Force (ignore the 15-day threshold)"},
    "checkbox_email_on_renew_failure": {"fr": "M'envoyer un email si le renouvellement échoue", "en": "Email me if renewal fails"},
    "btn_renew_cert": {"fr": "Renouveler le certificat", "en": "Renew certificate"},
    "btn_apply": {"fr": "Appliquer", "en": "Apply"},
    "h3_dns_auto_config": {"fr": "Configuration DNS automatique chez le registrar", "en": "Automatic DNS configuration at the registrar"},
    "dns_push_check_desc": {
        "fr": "Vérifie si la zone DNS chez le registrar correspond à la configuration suggérée par Wappos. Nécessite des identifiants API registrar configurés pour ce domaine.",
        "en": "Checks whether the DNS zone at the registrar matches Wappos's suggested configuration. Requires registrar API credentials configured for this domain.",
    },
    "btn_check_dns_sync": {"fr": "Vérifier la synchronisation DNS", "en": "Check DNS synchronization"},
    "dns_already_synced": {
        "fr": "Zone DNS déjà synchronisée avec la suggestion Wappos ({n} enregistrement(s) inchangé(s)).",
        "en": "DNS zone already synchronized with the Wappos suggestion ({n} unchanged record(s)).",
    },
    "dns_preview_summary": {
        "fr": "Aperçu (dry-run) : {create} à créer, {update} à mettre à jour, {delete} à supprimer.",
        "en": "Preview (dry-run): {create} to create, {update} to update, {delete} to delete.",
    },
    "th_action": {"fr": "Action", "en": "Action"},
    "th_record": {"fr": "Enregistrement DNS", "en": "DNS record"},
    "word_create": {"fr": "Créer", "en": "Create"},
    "word_update": {"fr": "Mettre à jour", "en": "Update"},
    "word_delete": {"fr": "Supprimer", "en": "Delete"},
    "not_managed_by_wappos": {"fr": "(non géré par Wappos)", "en": "(not managed by Wappos)"},
    "confirm_dns_push": {
        "fr": "Pousser réellement ces changements DNS chez le registrar de {domain} ? Cette action modifie de vrais enregistrements DNS.",
        "en": "Really push these DNS changes to {domain}'s registrar? This action modifies real DNS records.",
    },
    "checkbox_force_include_unmanaged": {
        "fr": "Forcer (inclure aussi les enregistrements non gérés par Wappos, ci-dessus)",
        "en": "Force (also include the records not managed by Wappos, above)",
    },
    "btn_apply_dns_changes": {"fr": "Appliquer réellement ces changements", "en": "Really apply these changes"},
    "h3_dns_suggested": {"fr": "Configuration DNS suggérée (pour saisie manuelle)", "en": "Suggested DNS configuration (for manual entry)"},
    "dns_suggested_note": {
        "fr": "Ceci est une recommandation basée sur la configuration actuelle du serveur — vérifiez-la avant de l'appliquer chez votre registrar, elle ne remplace pas votre propre jugement sur votre zone DNS.",
        "en": "This is a recommendation based on the server's current configuration — check it before applying it at your registrar, it does not replace your own judgment about your DNS zone.",
    },
    "dns_adjusted_for_relay_note": {
        "fr": "Ajustée par rapport à la suggestion Wappos native : ce domaine utilise un relais SMTP externe (SMTP2GO, réglage visible dans Réglages → Email). Le SPF a été complété avec {spf_include} et l'enregistrement DKIM local a été commenté (non utilisé — SMTP2GO signe avec sa propre clé, sélecteur propre à ce domaine à récupérer dans leur tableau de bord).",
        "en": "Adjusted from the native Wappos suggestion: this domain uses an external SMTP relay (SMTP2GO, setting visible in Settings → Email). SPF was completed with {spf_include} and the local DKIM record was commented out (unused — SMTP2GO signs with its own key, a selector specific to this domain to retrieve from their dashboard).",
    },
    "domain_is_main_note": {
        "fr": "Ce domaine est le domaine principal — il ne peut pas être supprimé tant que ce sera le cas (définissez un autre domaine comme principal d'abord).",
        "en": "This domain is the main domain — it cannot be removed while it holds that role (set another domain as main first).",
    },
    "domain_has_apps_note": {
        "fr": "Ce domaine ne peut pas être supprimé tant que des apps y sont installées — désinstallez-les d'abord :",
        "en": "This domain cannot be removed while apps are installed on it — uninstall them first:",
    },
    "confirm_delete_domain": {
        "fr": "Supprimer définitivement le domaine {domain} ? Cette action est irréversible.",
        "en": "Permanently delete the domain {domain}? This action is irreversible.",
    },
    "alert_type_domain_name": {
        "fr": "Pour supprimer ce domaine, tape exactement « {domain} » dans le champ prévu.",
        "en": "To delete this domain, type exactly \"{domain}\" in the field provided.",
    },
    "checkbox_keep_dyndns": {
        "fr": "Ne pas annuler l'enregistrement DynDNS de ce domaine (le laisse abonné au service)",
        "en": "Don't cancel this domain's DynDNS registration (keeps it subscribed to the service)",
    },
    "dyndns_recovery_password_label": {
        "fr": "Mot de passe de récupération DynDNS (optionnel, nécessaire si l'annulation de l'abonnement l'exige)",
        "en": "DynDNS recovery password (optional, needed if cancelling the subscription requires it)",
    },
    "type_word_to_confirm_generic": {"fr": "Tapez « {word} » pour confirmer", "en": "Type \"{word}\" to confirm"},
    "btn_delete_domain": {"fr": "Supprimer ce domaine", "en": "Delete this domain"},
    "domain_not_found": {"fr": "Domaine introuvable ou inaccessible.", "en": "Domain not found or unreachable."},
    "msg_config_applied": {"fr": "Configuration appliquée.", "en": "Configuration applied."},
    "msg_action_executed": {"fr": "Action exécutée.", "en": "Action executed."},
    "msg_main_domain_changed": {"fr": "Domaine principal changé.", "en": "Main domain changed."},
    "msg_cert_installed": {"fr": "Certificat installé.", "en": "Certificate installed."},
    "msg_cert_renewed": {"fr": "Certificat renouvelé.", "en": "Certificate renewed."},
    "msg_domain_removed": {"fr": "Domaine {domain} supprimé.", "en": "Domain {domain} removed."},
    "err_registrar_rejected": {
        "fr": "Le registrar a rejeté {n} enregistrement(s) DNS : {errors}",
        "en": "The registrar rejected {n} DNS record(s): {errors}",
    },
    "msg_dns_pushed_with_warnings": {
        "fr": "Configuration DNS poussée, avec {n} avertissement(s) : {warnings}",
        "en": "DNS configuration pushed, with {n} warning(s): {warnings}",
    },
    "msg_dns_pushed": {"fr": "Configuration DNS poussée chez le registrar.", "en": "DNS configuration pushed to the registrar."},

    "title_docker_add": {"fr": "Ajouter une app Docker", "en": "Add a Docker app"},
    "nav_docker_apps": {"fr": "Applications Docker", "en": "Docker apps"},
    "breadcrumb_add": {"fr": "Ajouter", "en": "Add"},
    "h3_step1_catalogue": {"fr": "1. Choisir dans le catalogue", "en": "1. Choose from the catalog"},
    "catalogue_intro": {
        "fr": "{n} applications connues, avec image/port/volume déjà renseignés. Tu ne trouves pas la tienne ? Utilise « Autre chose » ci-dessous.",
        "en": "{n} known applications, with image/port/volume already filled in. Can't find yours? Use \"Something else\" below.",
    },
    "catalogue_search_placeholder": {"fr": "Rechercher une app (ex. mots de passe, monitoring, wiki...)", "en": "Search for an app (e.g. passwords, monitoring, wiki...)"},
    "catalogue_unavailable_banner": {
        "fr": "Catalogue indisponible pour le moment (pas d'accès réseau ?) — utilise « Autre chose » ci-dessous.",
        "en": "Catalog unavailable right now (no network access?) — use \"Something else\" below.",
    },
    "manual_entry_summary": {"fr": "Autre chose : coller une image, une commande « docker run » ou un docker-compose.yml", "en": "Something else: paste an image, a \"docker run\" command, or a docker-compose.yml"},
    "manual_entry_desc": {
        "fr": "Colle juste le nom d'une image (ex. {example}) pour que Wappos essaie de détecter automatiquement le port et le volume de données qu'elle déclare, ou colle une commande « docker run »/un docker-compose.yml complet.",
        "en": "Just paste an image name (e.g. {example}) so Wappos tries to automatically detect the port and data volume it declares, or paste a full \"docker run\" command / docker-compose.yml.",
    },
    "smart_input_placeholder": {
        "fr": "ex. vaultwarden/server:latest\nou\ndocker run -d -p 8080:80 -v /data:/config lscr.io/linuxserver/heimdall\nou un docker-compose.yml complet",
        "en": "e.g. vaultwarden/server:latest\nor\ndocker run -d -p 8080:80 -v /data:/config lscr.io/linuxserver/heimdall\nor a full docker-compose.yml",
    },
    "smart_url_label": {"fr": "Ou une URL https:// vers un docker-compose.yml", "en": "Or an https:// URL to a docker-compose.yml"},
    "btn_analyze": {"fr": "Analyser", "en": "Analyze"},
    "compose_picker_desc": {
        "fr": "Ce docker-compose.yml déclare plusieurs services — choisis celui à exposer via Wappos/SSO. Les autres démarreront à ses côtés comme dépendances internes (base de données, cache...), non accessibles publiquement.",
        "en": "This docker-compose.yml declares several services — choose the one to expose via Wappos/SSO. The others will start alongside it as internal dependencies (database, cache...), not publicly accessible.",
    },
    "h3_step2_params": {"fr": "2. Paramètres", "en": "2. Parameters"},
    "label_exposure": {"fr": "Exposition", "en": "Exposure"},
    "radio_under_path": {"fr": "Sous un chemin d'un domaine existant", "en": "Under a path of an existing domain"},
    "radio_dedicated_subdomain": {"fr": "Sous-domaine dédié", "en": "Dedicated subdomain"},
    "label_domain": {"fr": "Domaine", "en": "Domain"},
    "label_path": {"fr": "Chemin", "en": "Path"},
    "label_subdomain": {"fr": "Sous-domaine", "en": "Subdomain"},
    "label_parent_domain": {"fr": "Domaine parent", "en": "Parent domain"},
    "label_visibility": {"fr": "Visibilité", "en": "Visibility"},
    "radio_admins_only": {"fr": "Administrateurs uniquement", "en": "Administrators only"},
    "radio_all_accounts": {"fr": "Tous les comptes", "en": "All accounts"},
    "radio_visitors_public": {"fr": "Visiteurs (public)", "en": "Visitors (public)"},
    "advanced_params_summary": {
        "fr": "Paramètres techniques (identifiant, image Docker, port, limites, variables d'environnement, fichiers de config...)",
        "en": "Technical parameters (identifier, Docker image, port, limits, environment variables, config files...)",
    },
    "label_slug": {"fr": "Identifiant (slug)", "en": "Identifier (slug)"},
    "slug_pattern_title": {"fr": "Lettres minuscules, chiffres et tirets uniquement", "en": "Lowercase letters, digits and hyphens only"},
    "slug_help": {"fr": "Nom technique interne, utilisé dans l'URL et les fichiers de l'app. Ex. « grafana ».", "en": "Internal technical name, used in the app's URL and files. E.g. \"grafana\"."},
    "label_docker_image": {"fr": "Image Docker", "en": "Docker image"},
    "image_help": {"fr": "Le paquet Docker à installer, trouvable sur hub.docker.com ou dans la doc de l'app.", "en": "The Docker package to install, found on hub.docker.com or in the app's documentation."},
    "label_container_port": {"fr": "Port du conteneur", "en": "Container port"},
    "port_help": {"fr": "Le port sur lequel l'app écoute à l'intérieur du conteneur (souvent détecté automatiquement).", "en": "The port the app listens on inside the container (often detected automatically)."},
    "label_data_path": {"fr": "Chemin des données dans le conteneur (optionnel)", "en": "Data path inside the container (optional)"},
    "label_url_env_var": {"fr": "Variable d'environnement pour l'URL publique (optionnel)", "en": "Environment variable for the public URL (optional)"},
    "label_cpu_limit": {"fr": "Limite CPU (optionnel)", "en": "CPU limit (optional)"},
    "cpu_limit_help": {"fr": "Nombre de cœurs maximum que le conteneur peut utiliser (ex. 0.5 = un demi-cœur).", "en": "Maximum number of cores the container can use (e.g. 0.5 = half a core)."},
    "label_mem_limit": {"fr": "Limite mémoire (optionnel)", "en": "Memory limit (optional)"},
    "mem_limit_help": {"fr": "Mémoire maximum autorisée, en méga-octets (m) ou giga-octets (g) — ex. 512m ou 1g. L'unité est obligatoire.", "en": "Maximum allowed memory, in megabytes (m) or gigabytes (g) — e.g. 512m or 1g. The unit is required."},
    "label_ldap_capable": {"fr": "Cette app sait s'authentifier via LDAP", "en": "This app can authenticate via LDAP"},
    "ldap_help": {
        "fr": "Injecte automatiquement LDAP_HOST/LDAP_PORT/LDAP_BASE_DN vers l'annuaire YunoHost. Ces noms de variables ne sont pas universels — vérifie dans la documentation de l'app installée le nom exact attendu, et adapte-le toi-même si besoin.",
        "en": "Automatically injects LDAP_HOST/LDAP_PORT/LDAP_BASE_DN pointing to the YunoHost directory. These variable names aren't universal — check the installed app's documentation for the exact expected name and adjust it yourself if needed.",
    },
    "ldap_connection_details_title": {"fr": "Valeurs à utiliser si l'app se configure via sa propre page LDAP (pas par variables d'environnement) :", "en": "Values to use if the app is configured via its own LDAP settings page (not environment variables):"},
    "ldap_connection_anonymous_bind": {"fr": "Connexion anonyme (pas d'identifiant ni mot de passe nécessaire)", "en": "Anonymous bind (no username or password needed)"},
    "label_env_vars": {"fr": "Variables d'environnement (une par ligne, KEY=valeur)", "en": "Environment variables (one per line, KEY=value)"},
    "label_config_files": {
        "fr": "Fichiers de configuration (optionnel — montés en lecture seule dans le conteneur, en plus du volume de données)",
        "en": "Configuration files (optional — mounted read-only in the container, in addition to the data volume)",
    },
    "btn_add_file": {"fr": "+ Ajouter un fichier", "en": "+ Add a file"},
    "btn_install_app": {"fr": "Installer", "en": "Install"},
    "btn_use_this_app": {"fr": "Utiliser cette app", "en": "Use this app"},
    "no_results_try_other": {"fr": "Aucun résultat — essaie « Autre chose » ci-dessus.", "en": "No results — try \"Something else\" above."},
    "catalogue_unavailable_short": {"fr": "Catalogue indisponible.", "en": "Catalog unavailable."},
    "you_are_installing": {"fr": "Vous installez : {name}", "en": "You are installing: {name}"},
    "config_file_path_placeholder": {"fr": "Chemin dans le conteneur, ex. /etc/prometheus/prometheus.yml", "en": "Path inside the container, e.g. /etc/prometheus/prometheus.yml"},
    "config_file_name_placeholder": {"fr": "Nom de fichier, ex. prometheus.yml", "en": "File name, e.g. prometheus.yml"},
    "config_file_content_placeholder": {"fr": "Contenu du fichier", "en": "File content"},
    "btn_remove_file": {"fr": "Retirer ce fichier", "en": "Remove this file"},
    "field_data_path_word": {"fr": "chemin de données", "en": "data path"},
    "field_env_vars_word": {"fr": "variables d'environnement", "en": "environment variables"},
    "field_url_var_word": {"fr": "variable d'URL", "en": "URL variable"},
    "companions_summary_prefix": {
        "fr": "Démarreront aussi comme dépendances internes (non exposés) : ",
        "en": "Will also start as internal dependencies (not exposed): ",
    },
    "detected_automatically": {"fr": "Détecté automatiquement : {fields}.", "en": "Automatically detected: {fields}."},
    "nothing_detected_automatically": {
        "fr": "Aucun champ n'a pu être détecté automatiquement, complète-les à la main.",
        "en": "No field could be detected automatically, fill them in manually.",
    },
    "data_path_not_declared": {
        "fr": "Chemin des données non déclaré par l'image — si l'app doit conserver des données entre redémarrages, renseigne-le toi-même dans « Options avancées » (voir la documentation de l'app).",
        "en": "Data path not declared by the image — if the app needs to keep data between restarts, fill it in yourself under \"Advanced options\" (see the app's documentation).",
    },
    "warnings_prefix": {"fr": "Avertissement(s) : {warnings}", "en": "Warning(s): {warnings}"},
    "analyzing": {"fr": "Analyse en cours…", "en": "Analyzing…"},
    "error_prefix": {"fr": "Erreur : {error}", "en": "Error: {error}"},
    "communication_error": {"fr": "Erreur de communication avec le serveur.", "en": "Communication error with the server."},
    "path_already_used_by": {"fr": "Déjà utilisé par « {name} ».", "en": "Already used by \"{name}\"."},
    "path_free": {"fr": "Libre.", "en": "Free."},
    "subdomain_free_will_create": {"fr": "{domain} — libre, sera créé.", "en": "{domain} — free, will be created."},
    "subdomain_exists_empty": {"fr": "{domain} — existe déjà, sans app installée, sera réutilisé.", "en": "{domain} — already exists, no app installed, will be reused."},
    "subdomain_exists_used": {"fr": "{domain} — déjà utilisé, choisissez un autre nom (ex. {suggestion}).", "en": "{domain} — already used, choose another name (e.g. {suggestion})."},

    "title_confirm_install": {"fr": "Confirmer l'installation", "en": "Confirm installation"},
    "breadcrumb_confirm": {"fr": "Confirmer", "en": "Confirm"},
    "h3_check_before_install": {"fr": "Vérifie avant d'installer", "en": "Check before installing"},
    "confirm_label_identifier": {"fr": "Identifiant :", "en": "Identifier:"},
    "confirm_label_image": {"fr": "Image :", "en": "Image:"},
    "confirm_label_container_port": {"fr": "Port du conteneur :", "en": "Container port:"},
    "confirm_label_public_address": {"fr": "Adresse publique :", "en": "Public address:"},
    "confirm_label_visible_to": {"fr": "Visible par :", "en": "Visible to:"},
    "confirm_label_persistent_data": {"fr": "Données persistantes :", "en": "Persistent data:"},
    "persistent_data_yes": {"fr": "Oui — un volume Docker sera créé pour {path}.", "en": "Yes — a Docker volume will be created for {path}."},
    "persistent_data_no": {
        "fr": "Non — aucun volume de données déclaré, l'app perdra ses données si le conteneur est recréé.",
        "en": "No — no data volume declared, the app will lose its data if the container is recreated.",
    },
    "confirm_label_env_vars": {"fr": "Variables d'environnement :", "en": "Environment variables:"},
    "env_vars_defined_count": {"fr": "{n} définie(s)", "en": "{n} defined"},
    "confirm_label_companions": {"fr": "Dépendances internes (non exposées) :", "en": "Internal dependencies (not exposed):"},
    "confirm_label_config_files": {"fr": "Fichiers de configuration montés :", "en": "Mounted configuration files:"},
    "confirm_label_resource_limits": {"fr": "Limites de ressources :", "en": "Resource limits:"},
    "mem_word": {"fr": "de mémoire", "en": "of memory"},
    "confirm_label_logo": {"fr": "Logo :", "en": "Logo:"},
    "logo_will_apply": {
        "fr": "celui du catalogue sera appliqué s'il est accessible, sinon une lettre de repli sera utilisée.",
        "en": "the one from the catalog will be applied if reachable, otherwise a fallback letter will be used.",
    },
    "confirm_label_ldap_wiring": {"fr": "Câblage LDAP :", "en": "LDAP wiring:"},
    "ldap_variables_injected": {"fr": "variables injectées —", "en": "variables injected —"},
    "btn_edit": {"fr": "Modifier", "en": "Edit"},
    "btn_confirm_install": {"fr": "Confirmer l'installation", "en": "Confirm installation"},

    "docker_not_installed": {
        "fr": "Docker n'est pas installé (ou son démon est injoignable) sur ce serveur — aucune app Docker ne peut être listée ou installée pour l'instant.",
        "en": "Docker is not installed (or its daemon is unreachable) on this server — no Docker app can be listed or installed for now.",
    },
    "btn_add_docker_app": {"fr": "+ Ajouter une app Docker", "en": "+ Add a Docker app"},
    "btn_audit_cleanup": {"fr": "Audit & nettoyage", "en": "Audit & cleanup"},
    "btn_check_updates": {"fr": "Vérifier les mises à jour", "en": "Check for updates"},
    "checking_updates": {"fr": "Vérification…", "en": "Checking…"},
    "container_not_found": {"fr": "conteneur introuvable", "en": "container not found"},
    "container_not_found_title": {"fr": "Le conteneur Docker attendu est introuvable", "en": "The expected Docker container was not found"},
    "resource_limits_title": {"fr": "Limites de ressources appliquées", "en": "Resource limits applied"},
    "update_available_badge": {"fr": "mise à jour disponible", "en": "update available"},
    "btn_logs": {"fr": "Logs", "en": "Logs"},
    "btn_edit_short": {"fr": "Modifier", "en": "Edit"},
    "btn_update": {"fr": "Mettre à jour", "en": "Update"},
    "btn_stop": {"fr": "Arrêter", "en": "Stop"},
    "btn_start": {"fr": "Démarrer", "en": "Start"},
    "btn_restart": {"fr": "Redémarrer", "en": "Restart"},
    "confirm_delete_docker_app": {"fr": "Supprimer {slug} ? Cette action est irréversible.", "en": "Delete {slug}? This action is irreversible."},
    "checkbox_purge_data": {"fr": "Purger les données", "en": "Purge data"},
    "btn_delete_short": {"fr": "Supprimer", "en": "Delete"},
    "btn_delete_group": {"fr": "Supprimer le groupe", "en": "Delete group"},
    "no_docker_app_tracked": {"fr": "Aucune app Docker suivie pour l'instant.", "en": "No Docker app tracked for now."},

    "title_edit_slug": {"fr": "Modifier {slug}", "en": "Edit {slug}"},
    "breadcrumb_edit_slug": {"fr": "Modifier — {slug}", "en": "Edit — {slug}"},
    "warning_edit_restarts_container": {
        "fr": "Toute modification des paramètres ci-dessous redémarre le conteneur — coupure de service le temps du redémarrage.",
        "en": "Any change to the settings below restarts the container — brief service interruption during the restart.",
    },
    "h3_change_url": {"fr": "Changer l'URL", "en": "Change URL"},
    "current_domain_path": {"fr": "Domaine et chemin actuels :", "en": "Current domain and path:"},
    "btn_change": {"fr": "Changer", "en": "Change"},
    "h3_params_of": {"fr": "Paramètres de {slug}", "en": "Parameters for {slug}"},
    "clear_field_removes_volume": {"fr": "Vider ce champ supprime le volume de données existant.", "en": "Clearing this field removes the existing data volume."},
    "btn_save_and_restart": {"fr": "Enregistrer et redémarrer", "en": "Save and restart"},
    "h3_access": {"fr": "Accès", "en": "Access"},
    "forbidden_for_group_title": {"fr": "Non autorisé pour ce groupe côté Wappos", "en": "Not allowed for this group on the Wappos side"},
    "h3_portal_tile_and_logo": {"fr": "Tuile portail et logo", "en": "Portal tile and logo"},
    "label_display_label": {"fr": "Libellé", "en": "Label"},
    "label_display_order": {"fr": "Ordre d'affichage", "en": "Display order"},
    "label_description": {"fr": "Description", "en": "Description"},
    "label_logo_png": {"fr": "Logo (PNG)", "en": "Logo (PNG)"},
    "checkbox_show_tile": {"fr": "Afficher la tuile dans le portail", "en": "Show the tile in the portal"},
    "checkbox_hide_from_public": {"fr": "Masquer de la liste publique", "en": "Hide from the public list"},
    "btn_save": {"fr": "Enregistrer", "en": "Save"},

    "title_docker_audit": {"fr": "Audit & nettoyage Docker", "en": "Docker audit & cleanup"},
    "h3_orphan_containers": {"fr": "Conteneurs orphelins ({n})", "en": "Orphan containers ({n})"},
    "unknown_image": {"fr": "image inconnue", "en": "unknown image"},
    "confirm_delete_container": {"fr": "Supprimer le conteneur {name} ?", "en": "Delete container {name}?"},
    "no_orphan_container": {"fr": "Aucun conteneur orphelin.", "en": "No orphan container."},
    "h3_orphan_volumes": {"fr": "Volumes orphelins ({n})", "en": "Orphan volumes ({n})"},
    "orphan_volumes_warning": {
        "fr": "Peuvent contenir de vraies données — suppression une par une uniquement, jamais en masse.",
        "en": "May contain real data — delete one at a time only, never in bulk.",
    },
    "confirm_delete_volume": {"fr": "Supprimer définitivement le volume {name} et toutes ses données ?", "en": "Permanently delete volume {name} and all its data?"},
    "no_orphan_volume": {"fr": "Aucun volume orphelin.", "en": "No orphan volume."},
    "h3_orphan_networks": {"fr": "Réseaux orphelins ({n})", "en": "Orphan networks ({n})"},
    "confirm_delete_network": {"fr": "Supprimer le réseau {name} ?", "en": "Delete network {name}?"},
    "no_orphan_network": {"fr": "Aucun réseau orphelin.", "en": "No orphan network."},
    "h3_unused_images": {"fr": "Images inutilisées ({n})", "en": "Unused images ({n})"},
    "images_total_size": {"fr": "{n} image(s), {size} Mo au total.", "en": "{n} image(s), {size} MB total."},
    "confirm_prune_images": {"fr": "Nettoyer les {n} image(s) inutilisée(s) ?", "en": "Clean up the {n} unused image(s)?"},
    "btn_prune_images": {"fr": "Nettoyer les images inutilisées", "en": "Clean up unused images"},
    "no_unused_image": {"fr": "Aucune image inutilisée.", "en": "No unused image."},
    "h3_empty_domains": {"fr": "Domaines sans app installée ({n})", "en": "Domains without an installed app ({n})"},
    "empty_domains_note": {
        "fr": "Signalés uniquement — jamais supprimés automatiquement (un domaine peut être utile sans app installée).",
        "en": "Reported only — never removed automatically (a domain can be useful without an installed app).",
    },
    "no_empty_domain": {"fr": "Aucun domaine vide.", "en": "No empty domain."},
    "h3_docker_ce_danger_zone": {"fr": "Docker CE — Zone dangereuse", "en": "Docker CE — Danger zone"},
    "docker_ce_installed_summary": {
        "fr": "Installé — {tracked} conteneur(s) suivi(s) par wappos_admin, {foreign} conteneur(s) étranger(s).",
        "en": "Installed — {tracked} container(s) tracked by wappos_admin, {foreign} foreign container(s).",
    },
    "warning_containers_exist": {"fr": "⚠️ Attention — des conteneurs existent sur ce serveur :", "en": "⚠️ Warning — containers exist on this server:"},
    "tracked_by_wappos_admin": {"fr": "(suivi par wappos_admin)", "en": "(tracked by wappos_admin)"},
    "foreign_not_managed": {"fr": "(étranger, non géré par wappos_admin)", "en": "(foreign, not managed by wappos_admin)"},
    "docker_ce_uninstall_warning": {
        "fr": "Désinstaller Docker CE arrête et détruit TOUS les conteneurs, y compris ceux suivis par wappos_admin (ex. Portainer) — pas seulement les conteneurs étrangers.",
        "en": "Uninstalling Docker CE stops and destroys ALL containers, including those tracked by wappos_admin (e.g. Portainer) — not just foreign containers.",
    },
    "confirm_uninstall_docker_ce": {
        "fr": "Désinstaller Docker CE et détruire tous les conteneurs, volumes et réseaux non externes ?",
        "en": "Uninstall Docker CE and destroy all non-external containers, volumes and networks?",
    },
    "btn_uninstall_docker_ce": {"fr": "Désinstaller Docker CE", "en": "Uninstall Docker CE"},
    "docker_ce_not_installed": {"fr": "Docker CE n'est pas installé sur ce serveur.", "en": "Docker CE is not installed on this server."},

    "title_logs_slug": {"fr": "Logs — {slug}", "en": "Logs — {slug}"},
    "btn_refresh": {"fr": "Actualiser", "en": "Refresh"},
    "btn_see_more_lines": {"fr": "Voir plus ({n} lignes)", "en": "See more ({n} lines)"},
    "h3_live_resources": {"fr": "Ressources en direct", "en": "Live resources"},
    "loading": {"fr": "Chargement…", "en": "Loading…"},
    "h3_last_n_lines": {"fr": "Dernières {n} lignes", "en": "Last {n} lines"},
    "no_log_available": {"fr": "Aucun log disponible.", "en": "No log available."},
    "stats_unavailable": {"fr": "Statistiques indisponibles.", "en": "Statistics unavailable."},
    "container_stopped_no_stats": {"fr": "Conteneur arrêté — pas de statistiques.", "en": "Container stopped — no statistics."},
    "label_network_cumulative": {"fr": "Réseau (cumulé)", "en": "Network (cumulative)"},

    "action_label_install": {"fr": "Installation", "en": "Installation"},
    "action_label_update": {"fr": "Mise à jour", "en": "Update"},
    "action_label_edit": {"fr": "Édition", "en": "Edit"},
    "progress_title": {"fr": "{action} Docker — {slug}", "en": "{action} Docker — {slug}"},
    "progress_header": {"fr": "{action} de {slug}", "en": "{action} of {slug}"},
    "progress_success": {"fr": "{action} terminée avec succès.", "en": "{action} completed successfully."},
    "progress_warning_header": {"fr": "{action} terminée — points à vérifier :", "en": "{action} completed — points to check:"},
    "btn_back_to_docker": {"fr": "Retour à Docker", "en": "Back to Docker"},
    "progress_not_found": {"fr": "Suivi de progression introuvable (le service a peut-être redémarré).", "en": "Progress tracking not found (the service may have restarted)."},

    "title_update_slug": {"fr": "Mettre à jour {slug}", "en": "Update {slug}"},
    "breadcrumb_update_slug": {"fr": "Mise à jour — {slug}", "en": "Update — {slug}"},
    "warning_update_restarts_container": {
        "fr": "Une mise à jour redémarre le conteneur — coupure de service le temps du redémarrage.",
        "en": "An update restarts the container — brief service interruption during the restart.",
    },
    "h3_current_version": {"fr": "Version actuelle", "en": "Current version"},
    "h3_choose_new_version": {"fr": "Choisir une nouvelle version", "en": "Choose a new version"},
    "no_version_found": {"fr": "Aucune version trouvée pour cette image.", "en": "No version found for this image."},
    "tag_last_updated": {"fr": " (dernière mise à jour : {date})", "en": " (last updated: {date})"},
    "btn_update_to_version": {"fr": "Mettre à jour vers cette version", "en": "Update to this version"},
    "h3_pull_latest_tag": {"fr": "Ou récupérer la dernière version du tag actuel", "en": "Or pull the latest version of the current tag"},
    "pull_latest_tag_desc": {
        "fr": "Sans changer le tag référencé ({image}) — utile si ce tag est flottant (ex. {example}).",
        "en": "Without changing the referenced tag ({image}) — useful if this tag is floating (e.g. {example}).",
    },
    "btn_pull_latest_tag": {"fr": "Récupérer la dernière version de ce tag", "en": "Pull the latest version of this tag"},

    "nav_users": {"fr": "Utilisateurs", "en": "Users"},
    "no_user": {"fr": "Aucun utilisateur.", "en": "No user."},
    "h3_user_list": {"fr": "Comptes", "en": "Accounts"},
    "role_superadmin": {"fr": "Superadmin", "en": "Superadmin"},
    "role_domain_admin": {"fr": "Admin de domaine : {domains}", "en": "Domain admin: {domains}"},
    "label_account_role": {"fr": "Rôle / autorisation", "en": "Role / permission"},
    "option_no_particular_role": {"fr": "Utilisateur standard", "en": "Standard user"},
    "role_option_superadmin": {"fr": "Super-administrateur (accès total)", "en": "Super-administrator (full access)"},
    "role_option_domain_admin": {"fr": "Administrateur de domaine", "en": "Domain administrator"},
    "role_option_visitor": {"fr": "Visiteur", "en": "Visitor"},
    "confirm_create_superadmin_account": {"fr": "Ce compte aura un accès superadmin complet au serveur, sur tous les domaines. Confirmer ?", "en": "This account will have full superadmin access to the server, across all domains. Confirm?"},
    "err_user_created_role_failed": {"fr": "Compte {username} créé, mais l'attribution du rôle a échoué : {error}", "en": "Account {username} created, but role assignment failed: {error}"},
    "msg_user_created_domain_admin_next_step": {"fr": "Compte {username} créé en tant qu'administrateur de domaine. N'oubliez pas de définir ses domaines possédés et son domaine principal sur la page Groupes.", "en": "Account {username} created as a domain administrator. Don't forget to set its owned domains and primary domain on the Groups page."},
    "role_domain_admin_no_domain": {"fr": "aucun domaine attribué", "en": "no domain assigned"},
    "h3_add_account": {"fr": "Ajouter un compte", "en": "Add an account"},
    "add_account_desc": {
        "fr": "Les comptes sont créés avec une adresse email au format username@domain.tld. Des alias d'email et des transferts d'emails supplémentaires peuvent être ajoutés ultérieurement par un administrateur ou l'utilisateur du compte lui même.",
        "en": "Accounts are created with an email address in the format username@domain.tld. Additional email aliases and forwards can be added later by an administrator or by the account's own user.",
    },
    "label_account_name": {"fr": "Nom du compte", "en": "Account name"},
    "account_name_pattern_title": {"fr": "Lettres minuscules, chiffres, _ et . uniquement", "en": "Lowercase letters, digits, _ and . only"},
    "label_full_name": {"fr": "Nom complet", "en": "Full name"},
    "label_password": {"fr": "Mot de passe", "en": "Password"},
    "aria_show_password_generic": {"fr": "Afficher le mot de passe", "en": "Show password"},
    "password_requirements_generic": {"fr": "8 caractères minimum. Robustesse exacte requise selon le réglage du serveur.", "en": "8 characters minimum. Exact strength required depends on the server's setting."},
    "label_confirm_password": {"fr": "Confirmer le mot de passe", "en": "Confirm password"},
    "passwords_mismatch_inline": {"fr": "Les mots de passe ne correspondent pas.", "en": "Passwords do not match."},
    "btn_add_account": {"fr": "Ajouter un compte", "en": "Add an account"},
    "h3_export_import_csv": {"fr": "Export / import CSV", "en": "CSV export / import"},
    "btn_export_csv": {"fr": "Exporter en CSV", "en": "Export as CSV"},
    "label_csv_file": {"fr": "Fichier CSV", "en": "CSV file"},
    "checkbox_update_existing_accounts": {"fr": "Mettre à jour les comptes existants présents dans le fichier", "en": "Update existing accounts found in the file"},
    "checkbox_delete_missing_accounts": {"fr": "Supprimer les comptes absents du fichier", "en": "Delete accounts missing from the file"},
    "btn_import": {"fr": "Importer", "en": "Import"},
    "confirm_import_delete_accounts": {
        "fr": "Tous les comptes absents de ce fichier CSV vont être supprimés définitivement. Cette action est irréversible. Continuer ?",
        "en": "All accounts missing from this CSV file will be permanently deleted. This action is irreversible. Continue?",
    },

    "title_edit_username": {"fr": "Modifier — {username}", "en": "Edit — {username}"},
    "h2_edit_username": {"fr": "Modifier {username}", "en": "Edit {username}"},
    "label_primary_email": {"fr": "Adresse email principale", "en": "Primary email address"},
    "label_confirm_email": {"fr": "Confirmer l'adresse email", "en": "Confirm email address"},
    "emails_mismatch": {"fr": "Les adresses ne correspondent pas.", "en": "The addresses do not match."},
    "label_mailbox_quota": {"fr": "Quota de messagerie", "en": "Mailbox quota"},
    "mailbox_quota_desc": {
        "fr": "Quota de messagerie : définissez une taille limite de stockage pour vos courriels, en mégaoctets (Mo). Mettre 0 pour la désactiver (illimité). Utilisation actuelle : {usage}.",
        "en": "Mailbox quota: set a storage size limit for your emails, in megabytes (MB). Set 0 to disable it (unlimited). Current usage: {usage}.",
    },
    "label_email_aliases": {"fr": "Alias d'email", "en": "Email aliases"},
    "email_aliases_desc": {
        "fr": "Des adresses supplémentaires qui reçoivent le courrier de ce compte, en plus de l'adresse principale.",
        "en": "Additional addresses that receive this account's mail, in addition to the primary address.",
    },
    "btn_add_alias": {"fr": "Ajouter un alias", "en": "Add an alias"},
    "label_email_forwards": {"fr": "Transferts d'email", "en": "Email forwards"},
    "email_forwards_desc": {
        "fr": "Les emails reçus sur ce compte sont automatiquement copiés vers ces adresses externes, en plus d'arriver dans la boîte du compte.",
        "en": "Emails received on this account are automatically copied to these external addresses, in addition to arriving in the account's mailbox.",
    },
    "btn_add_forward": {"fr": "Ajouter un transfert", "en": "Add a forward"},
    "h3_new_password": {"fr": "Nouveau mot de passe", "en": "New password"},
    "label_new_password": {"fr": "Nouveau mot de passe", "en": "New password"},
    "label_confirm_new_password": {"fr": "Confirmer le nouveau mot de passe", "en": "Confirm new password"},
    "h3_ssh_keys": {"fr": "Clés SSH", "en": "SSH keys"},
    "ssh_keys_desc": {
        "fr": "Permettent à ce compte de se connecter au serveur en SSH sans mot de passe, en s'identifiant avec sa clé publique.",
        "en": "Allow this account to connect to the server via SSH without a password, by identifying itself with its public key.",
    },
    "th_comment": {"fr": "Commentaire", "en": "Comment"},
    "th_key": {"fr": "Clé", "en": "Key"},
    "confirm_delete_ssh_key": {"fr": "Supprimer cette clé SSH ?", "en": "Delete this SSH key?"},
    "no_ssh_key_registered": {"fr": "Aucune clé SSH enregistrée.", "en": "No SSH key registered."},
    "label_new_public_key": {"fr": "Nouvelle clé publique", "en": "New public key"},
    "ssh_key_pattern_title": {"fr": "Une seule clé SSH publique (type + base64), sans saut de ligne", "en": "A single public SSH key (type + base64), no line break"},
    "label_comment_optional": {"fr": "Commentaire (optionnel)", "en": "Comment (optional)"},
    "btn_add_key": {"fr": "Ajouter la clé", "en": "Add key"},
    "checkbox_purge_account_data": {"fr": "Purger aussi les données du compte", "en": "Also purge the account's data"},
    "delete_account_note": {
        "fr": "Sans cette case, seul le compte est supprimé du serveur — les fichiers (/home/{username}) et les emails (/var/mail/{username}) restent sur le disque. Avec la case cochée, ils sont effacés définitivement en même temps que le compte.",
        "en": "Without this box, only the account is removed from the server — files (/home/{username}) and emails (/var/mail/{username}) stay on disk. With the box checked, they are permanently erased along with the account.",
    },
    "btn_delete_account": {"fr": "Supprimer ce compte", "en": "Delete this account"},
    "confirm_old_email_not_kept": {
        "fr": "L'ancienne adresse ({email}) ne sera pas conservée en alias — elle sera définitivement perdue. Continuer ?",
        "en": "The old address ({email}) will not be kept as an alias — it will be permanently lost. Continue?",
    },
    "confirm_delete_account_purge": {
        "fr": "Supprimer définitivement {username} ET purger ses données (/home, /var/mail) ? Cette action est irréversible.",
        "en": "Permanently delete {username} AND purge their data (/home, /var/mail)? This action is irreversible.",
    },
    "confirm_delete_account_simple": {"fr": "Supprimer définitivement {username} ?", "en": "Permanently delete {username}?"},

    "nav_groups": {"fr": "Groupes", "en": "Groups"},
    "breadcrumb_groups_perms": {"fr": "Groupes et autorisations", "en": "Groups and permissions"},
    "group_admins_label": {"fr": "Administrateurs", "en": "Administrators"},
    "group_all_users_label": {"fr": "Utilisateurs enregistrés", "en": "Registered users"},
    "group_visitors_label": {"fr": "Visiteurs", "en": "Visitors"},
    "group_domain_admins_label": {"fr": "Administrateurs de domaines", "en": "Domain administrators"},
    "group_named": {"fr": "Groupe '{name}'", "en": "Group '{name}'"},
    "confirm_delete_group": {"fr": "Voulez-vous vraiment supprimer {name} ?", "en": "Do you really want to delete {name}?"},
    "label_accounts": {"fr": "Comptes", "en": "Accounts"},
    "group_explain_admins": {
        "fr": "Les comptes affectés à ce groupe ont tous les droits sur le serveur (modification, création, ajout et suppression). Ils peuvent donc accéder à toutes les fonctionnalités, se connecter au serveur avec SSH et utiliser la commande sudo. N'ajoutez dans ce groupe que des comptes de personnes en qui vous avez absolument confiance !",
        "en": "Accounts assigned to this group have full rights on the server (modification, creation, addition and deletion). They can therefore access every feature, connect to the server via SSH and use the sudo command. Only add accounts of people you fully trust to this group!",
    },
    "group_explain_all_users": {"fr": "Groupe contenant tous les comptes des personnes inscrites/enregistrées sur le serveur.", "en": "Group containing all accounts of people registered on the server."},
    "group_explain_visitors": {"fr": "Permissions des visiteurs anonymes (non enregistrés).", "en": "Permissions for anonymous (unregistered) visitors."},
    "group_explain_visitors_note": {
        "fr": "Veillez à ce que certaines applications soient autorisées pour les visiteurs si vous avez l'intention de les utiliser avec des clients externes.",
        "en": "Make sure some applications are allowed for visitors if you intend to use them with external clients.",
    },
    "group_explain_wappos_domain_admins": {
        "fr": "Groupe technique Wappos : les comptes ajoutés ici peuvent devenir des administrateurs de domaine (scopés à un ou plusieurs domaines, voir la page de détail d'un domaine). Ce groupe est protégé et ne peut pas être supprimé.",
        "en": "Wappos technical group: accounts added here can become domain admins (scoped to one or more domains, see a domain's detail page). This group is protected and cannot be deleted.",
    },
    "btn_save_accounts": {"fr": "Enregistrer les comptes", "en": "Save accounts"},
    "label_permissions": {"fr": "Permissions", "en": "Permissions"},
    "err_domain_admins_group_no_shared_permissions": {
        "fr": "Les permissions ne se règlent plus sur le groupe wappos_domain_admins pour éviter un accès identique pour tous les admins de domaine. Utilisez la section \"Gérer les autorisations d'un compte individuel\" pour chaque compte.",
        "en": "Permissions can no longer be set on the wappos_domain_admins group, to avoid identical access for every domain admin. Use the \"Manage an individual account's permissions\" section for each account instead.",
    },
    "domain_admins_group_permissions_moved": {
        "fr": "Les permissions d'applications ne se règlent plus ici pour éviter que tous les admins de domaine reçoivent le même accès. Utilisez la section \"Gérer les autorisations d'un compte individuel\" plus bas pour régler l'accès compte par compte.",
        "en": "Application permissions are no longer set here, to avoid every domain admin receiving identical access. Use the \"Manage an individual account's permissions\" section below to set access account by account.",
    },
    "btn_save_permissions": {"fr": "Enregistrer les permissions", "en": "Save permissions"},
    "h3_individual_account_perms": {"fr": "Autorisations pour des comptes individuels", "en": "Permissions for individual accounts"},
    "label_add_account": {"fr": "Ajouter un compte", "en": "Add an account"},
    "select_account_placeholder": {"fr": "-- Sélectionner un compte --", "en": "-- Select an account --"},
    "select_account_to_manage": {"fr": "Sélectionnez un compte ci-dessus pour gérer ses permissions individuelles.", "en": "Select an account above to manage its individual permissions."},
    "h3_add_group": {"fr": "Ajouter un groupe", "en": "Add a group"},
    "group_name_desc": {"fr": "Uniquement des minuscules, des chiffres et des tirets bas (ex. {example}).", "en": "Lowercase letters, digits and underscores only (e.g. {example})."},
    "label_group_name": {"fr": "Nom du groupe", "en": "Group name"},
    "group_name_pattern_title": {"fr": "Minuscules, chiffres et tirets bas uniquement (pas d'espace ni de majuscule)", "en": "Lowercase letters, digits and underscores only (no spaces or uppercase)"},
    "btn_add_group": {"fr": "Ajouter un groupe", "en": "Add a group"},
    "h3_permission_detail": {"fr": "Détail des permissions", "en": "Permission detail"},
    "th_permission": {"fr": "Permission", "en": "Permission"},
    "th_effective_users": {"fr": "Comptes autorisés", "en": "Authorized accounts"},
    "perm_domain_system": {"fr": "Permissions système (sans domaine)", "en": "System permissions (no domain)"},
    "perm_no_users": {"fr": "Aucun compte autorisé", "en": "No authorized account"},
    "perm_all_accounts": {"fr": "Tous les comptes ({n})", "en": "All accounts ({n})"},
    "confirm_grant_dangerous_perm": {
        "fr": "Voulez-vous vraiment accorder l'accès à {perms} à « {group} » ? Un tel accès augmente considérablement la surface d'attaque si ce groupe se trouve être malveillant.",
        "en": "Do you really want to grant access to {perms} to \"{group}\"? Such access considerably increases the attack surface if this group turns out to be malicious.",
    },
    "confirm_remove_self_from_admins": {"fr": "Êtes-vous sûr de vouloir vous retirer du groupe « admins » ?", "en": "Are you sure you want to remove yourself from the \"admins\" group?"},
    "err_api_unreachable": {"fr": "L'API Wappos est injoignable.", "en": "The Wappos API is unreachable."},

    "err_group_name_empty": {"fr": "Le nom du groupe ne peut pas être vide.", "en": "The group name cannot be empty."},
    "msg_group_created": {"fr": "Groupe {name} créé.", "en": "Group {name} created."},
    "msg_group_deleted": {"fr": "Groupe {name} supprimé.", "en": "Group {name} deleted."},
    "msg_group_members_updated": {"fr": "Membres du groupe {name} mis à jour.", "en": "Members of group {name} updated."},
    "msg_domain_admin_owned_domains_updated": {"fr": "Domaines de {username} mis à jour.", "en": "{username}'s domains updated."},
    "h3_domain_admin_owned_domains": {"fr": "Domaines attribués", "en": "Assigned domains"},
    "domain_admin_owned_domains_info": {
        "fr": "Pour chaque compte de ce groupe, cochez le ou les domaines dont il est administrateur.",
        "en": "For each account in this group, tick the domain(s) it administers.",
    },
    "btn_save_domain_admin_owned_domains": {"fr": "Enregistrer les domaines", "en": "Save domains"},
    "label_primary_domain": {"fr": "Domaine principal", "en": "Primary domain"},
    "option_primary_domain_unset": {"fr": "— aucun —", "en": "— none —"},
    "primary_domain_info": {
        "fr": "Seul ce domaine permet à ce compte de se connecter à l'interface d'administration.",
        "en": "Only this domain lets this account log in to the administration interface.",
    },
    "th_domain_admin_account": {"fr": "Compte", "en": "Account"},
    "th_domain_admin_owned": {"fr": "Domaines possédés", "en": "Owned domains"},
    "th_domain_admin_primary": {"fr": "Principal", "en": "Primary"},
    "domain_admin_overview_no_domains": {"fr": "aucun", "en": "none"},
    "domain_admin_overview_no_primary": {"fr": "non défini", "en": "not set"},
    "star_set_as_primary": {"fr": "Définir comme domaine principal", "en": "Set as primary domain"},
    "star_is_primary": {"fr": "Domaine principal", "en": "Primary domain"},
    "label_filter_domain_admins": {"fr": "Filtrer par compte ou domaine...", "en": "Filter by account or domain..."},
    "domain_admin_no_search_results": {"fr": "Aucun compte ne correspond à ce filtre.", "en": "No account matches this filter."},
    "msg_group_permissions_updated": {"fr": "Permissions du groupe {name} mises à jour.", "en": "Permissions of group {name} updated."},
    "msg_permission_access_updated": {"fr": "Accès de « {permission} » mis à jour.", "en": "Access for \"{permission}\" updated."},
    "err_tile_not_enabled": {
        "fr": "Propriétés de {permission} mises à jour, mais « Afficher la tuile » n'a pas pu être activé (Wappos l'ignore pour une permission sans URL).",
        "en": "Properties of {permission} updated, but \"Show tile\" could not be enabled (Wappos ignores it for a permission without a URL).",
    },
    "msg_permission_properties_updated": {"fr": "Propriétés de {permission} mises à jour.", "en": "Properties of {permission} updated."},
    "err_no_csv_file": {"fr": "Aucun fichier CSV fourni.", "en": "No CSV file provided."},
    "import_summary": {"fr": "{created} créé(s), {updated} mis à jour, {deleted} supprimé(s)", "en": "{created} created, {updated} updated, {deleted} deleted"},
    "import_summary_with_errors": {"fr": "{summary}, {errors} en échec", "en": "{summary}, {errors} failed"},
    "err_import_failed": {"fr": "Import échoué : {summary}.", "en": "Import failed: {summary}."},
    "err_import_partial": {"fr": "Import partiellement réussi : {summary}.", "en": "Import partially successful: {summary}."},
    "msg_import_success": {"fr": "Import réussi : {summary}.", "en": "Import successful: {summary}."},
    "err_ssh_key_empty": {"fr": "La clé SSH ne peut pas être vide.", "en": "The SSH key cannot be empty."},
    "err_ssh_key_single_only": {"fr": "Une seule clé SSH à la fois (pas de saut de ligne).", "en": "Only one SSH key at a time (no line break)."},
    "err_ssh_key_format": {"fr": "Format de clé SSH non reconnu (attendu : type + clé en base64).", "en": "Unrecognized SSH key format (expected: type + base64 key)."},
    "msg_ssh_key_added": {"fr": "Clé SSH ajoutée.", "en": "SSH key added."},
    "msg_ssh_key_removed": {"fr": "Clé SSH supprimée.", "en": "SSH key removed."},
    "err_emails_mismatch": {"fr": "Les adresses email ne correspondent pas.", "en": "The email addresses do not match."},
    "err_nothing_changed": {"fr": "Vous n'avez rien modifié.", "en": "You haven't changed anything."},
    "msg_account_updated": {"fr": "Compte {username} mis à jour.", "en": "Account {username} updated."},
    "err_new_password_empty": {"fr": "Le nouveau mot de passe ne peut pas être vide.", "en": "The new password cannot be empty."},
    "msg_password_of_updated": {"fr": "Mot de passe de {username} mis à jour.", "en": "Password of {username} updated."},
    "err_all_fields_required": {"fr": "Tous les champs sont obligatoires pour créer un utilisateur.", "en": "All fields are required to create a user."},
    "msg_user_created": {"fr": "Utilisateur {username} créé.", "en": "User {username} created."},
    "msg_user_deleted": {"fr": "Utilisateur {username} supprimé.", "en": "User {username} deleted."},

    "time_never": {"fr": "jamais", "en": "never"},
    "time_ago_seconds": {"fr": "il y a quelques secondes", "en": "a few seconds ago"},
    "time_ago_minutes": {"fr": "il y a {n} minute{s}", "en": "{n} minute{s} ago"},
    "time_ago_hours": {"fr": "il y a {n} heure{s}", "en": "{n} hour{s} ago"},
    "time_ago_days": {"fr": "il y a {n} jour{s}", "en": "{n} day{s} ago"},
    "time_duration_seconds": {"fr": "quelques secondes", "en": "a few seconds"},
    "time_duration_minutes": {"fr": "{n} minute{s}", "en": "{n} minute{s}"},
    "time_duration_hours": {"fr": "{n} heure{s}", "en": "{n} hour{s}"},
    "time_duration_days": {"fr": "{n} jour{s}", "en": "{n} day{s}"},
    "value_unknown_lower": {"fr": "inconnu", "en": "unknown"},
    "service_substate_running": {"fr": "En cours d'exécution", "en": "Running"},
    "service_substate_exited": {"fr": "Terminé (oneshot)", "en": "Exited (oneshot)"},
    "service_substate_dead": {"fr": "Arrêté", "en": "Stopped"},
    "service_substate_failed": {"fr": "En échec", "en": "Failed"},
    "service_substate_activating": {"fr": "Démarrage en cours", "en": "Starting"},
    "service_substate_deactivating": {"fr": "Arrêt en cours", "en": "Stopping"},
    "service_substate_reload": {"fr": "Rechargement en cours", "en": "Reloading"},
    "service_substate_unknown": {"fr": "Inconnu", "en": "Unknown"},
    "unit_result_success": {"fr": "Succès", "en": "Success"},
    "unit_result_resources": {"fr": "Ressources indisponibles", "en": "Resources unavailable"},
    "unit_result_timeout": {"fr": "Délai dépassé", "en": "Timed out"},
    "unit_result_exit_code": {"fr": "Code de sortie non nul", "en": "Non-zero exit code"},
    "unit_result_signal": {"fr": "Arrêté par un signal", "en": "Stopped by a signal"},
    "unit_result_core_dump": {"fr": "Crash (core dump)", "en": "Crash (core dump)"},
    "unit_result_watchdog": {"fr": "Timeout du watchdog", "en": "Watchdog timeout"},
    "unit_result_start_limit_hit": {"fr": "Trop de redémarrages", "en": "Too many restarts"},
    "unit_result_oom_kill": {"fr": "Tué par manque de mémoire (OOM)", "en": "Killed for lack of memory (OOM)"},
    "unit_result_protocol": {"fr": "Erreur de protocole", "en": "Protocol error"},
    "unit_result_unknown": {"fr": "inconnu", "en": "unknown"},
    "month_01": {"fr": "janvier", "en": "January"}, "month_02": {"fr": "février", "en": "February"},
    "month_03": {"fr": "mars", "en": "March"}, "month_04": {"fr": "avril", "en": "April"},
    "month_05": {"fr": "mai", "en": "May"}, "month_06": {"fr": "juin", "en": "June"},
    "month_07": {"fr": "juillet", "en": "July"}, "month_08": {"fr": "août", "en": "August"},
    "month_09": {"fr": "septembre", "en": "September"}, "month_10": {"fr": "octobre", "en": "October"},
    "month_11": {"fr": "novembre", "en": "November"}, "month_12": {"fr": "décembre", "en": "December"},
    "day_label_fr_format": {"fr": "{day} {month} {year}", "en": "{month} {day}, {year}"},

    "domain_owners_no_candidates": {"fr": "Aucun compte n'est membre du groupe wappos_domain_admins pour l'instant. Ajoutez-en un depuis la page Groupes et autorisations.", "en": "No account is a member of the wappos_domain_admins group yet. Add one from the Groups and permissions page."},
    "h3_add_domain": {"fr": "Ajouter un domaine", "en": "Add a domain"},
    "btn_add": {"fr": "Ajouter", "en": "Add"},
    "checkbox_install_letsencrypt": {"fr": "Installer un certificat Let's Encrypt automatiquement", "en": "Automatically install a Let's Encrypt certificate"},
    "dyndns_options_summary": {"fr": "Options réservées aux domaines DynDNS *.nohost.me/*.noho.st/*.ynh.fr", "en": "Options reserved for DynDNS domains *.nohost.me/*.noho.st/*.ynh.fr"},
    "dyndns_recovery_password_placeholder": {"fr": "Mot de passe de récupération DynDNS", "en": "DynDNS recovery password"},
    "add_domain_dns_note": {"fr": "Le domaine doit déjà pointer vers ce serveur (DNS) pour que le certificat Let's Encrypt puisse être installé.", "en": "The domain must already point to this server (DNS) for the Let's Encrypt certificate to be installable."},
    "h3_local_network_access": {"fr": "Accès réseau local", "en": "Local network access"},
    "link_learn_more": {"fr": "En savoir plus", "en": "Learn more"},
    "local_access_no_adguard_short": {"fr": "AdGuard Home n'est pas installé.", "en": "AdGuard Home is not installed."},
    "install_adguard_link": {"fr": "installez AdGuard Home", "en": "install AdGuard Home"},
    "local_access_enabled": {
        "fr": "Activé — ces domaines sont accessibles depuis le réseau local sur tous les appareils.",
        "en": "Enabled — these domains are accessible from the local network on every device.",
    },
    "confirm_remove_local_domain": {
        "fr": "Retirer le domaine local {domain} ? La réécriture DNS AdGuard associée sera retirée aussi.",
        "en": "Remove local domain {domain}? The associated AdGuard DNS rewrite will be removed too.",
    },
    "btn_remove": {"fr": "Retirer", "en": "Remove"},
    "badge_active": {"fr": "Actif", "en": "Active"},
    "add_another_local_domain": {"fr": "Ajouter un autre domaine local", "en": "Add another local domain"},
    "local_domain_pattern_title": {"fr": "Un seul niveau, se terminant par .lan (ex. wappos.lan)", "en": "A single level, ending in .lan (e.g. wappos.lan)"},
    "local_access_disabled_short": {"fr": "Désactivé.", "en": "Disabled."},
    "btn_enable_local_access": {"fr": "Activer l'accès réseau local (wappos.lan)", "en": "Enable local network access (wappos.lan)"},
    "cert_valid_days": {"fr": "Certificat valide {n} jour{s}", "en": "Certificate valid {n} day{s}"},
    "no_domain": {"fr": "Aucun domaine.", "en": "No domain."},

    "title_home": {"fr": "Accueil", "en": "Home"},
    "quick_add": {"fr": "+ Ajout rapide", "en": "+ Quick add"},
    "quick_add_account": {"fr": "+ Ajouter un compte", "en": "+ Add an account"},
    "quick_add_domain": {"fr": "+ Ajouter un domaine", "en": "+ Add a domain"},
    "quick_add_group": {"fr": "+ Ajouter un groupe", "en": "+ Add a group"},
    "quick_install_app": {"fr": "+ Installer une app", "en": "+ Install an app"},
    "nav_groups_perms": {"fr": "Groupes et autorisations", "en": "Groups and permissions"},
    "nav_applications": {"fr": "Applications", "en": "Applications"},
    "nav_system_apps": {"fr": "Applications système", "en": "System applications"},
    "nav_diagnosis": {"fr": "Diagnostic", "en": "Diagnosis"},
    "nav_environment_health": {"fr": "Santé de mon environnement", "en": "My environment's health"},
    "title_environment_health": {"fr": "Santé de mon environnement", "en": "My environment's health"},
    "h3_certificates": {"fr": "Certificats", "en": "Certificates"},
    "cert_days_left": {"fr": "{days} jours restants", "en": "{days} days left"},
    "no_domain_in_scope": {"fr": "Aucun domaine.", "en": "No domain."},
    "h3_diagnosis_summary": {"fr": "Diagnostic", "en": "Diagnosis"},
    "count_errors": {"fr": "{n} erreur(s)", "en": "{n} error(s)"},
    "count_warnings": {"fr": "{n} avertissement(s)", "en": "{n} warning(s)"},
    "link_view_full_diagnosis": {"fr": "Voir le diagnostic complet", "en": "View full diagnosis"},
    "h3_disk_usage_by_app": {"fr": "Espace disque par application", "en": "Disk usage per application"},
    "disk_usage_help": {
        "fr": "Espace occupé par le code de chaque application. Certaines apps stockent leurs données ailleurs (ex. fichiers utilisateurs) et ne sont pas comptées ici.",
        "en": "Space used by each app's own code directory. Some apps store their data elsewhere (e.g. user files) and it isn't counted here.",
    },
    "no_disk_usage_data": {"fr": "Aucune donnée disponible.", "en": "No data available."},
    "h3_docker_containers": {"fr": "Conteneurs Docker", "en": "Docker containers"},
    "no_docker_container": {"fr": "Aucun conteneur Docker.", "en": "No Docker container."},
    "nav_backups": {"fr": "Sauvegardes", "en": "Backups"},
    "nav_database": {"fr": "Bases de données", "en": "Databases"},
    "database_page_intro": {
        "fr": "Accédez directement à la base de données de vos applications via Adminer, sans jamais voir le mot de passe complet.",
        "en": "Access your applications' databases directly via Adminer, without ever seeing the full password.",
    },
    "database_no_apps": {"fr": "Aucune application avec une base de données dans votre périmètre.", "en": "No app with a database in your scope."},
    "btn_database_connect": {"fr": "Se connecter", "en": "Connect"},
    "database_connecting": {"fr": "Connexion à Adminer en cours…", "en": "Connecting to Adminer…"},
    "database_connect_needs_js": {
        "fr": "JavaScript est requis pour cette connexion automatique.",
        "en": "JavaScript is required for this automatic connection.",
    },
    "database_connect_failed": {"fr": "La connexion automatique a échoué.", "en": "The automatic connection failed."},
    "database_adminer_not_installed": {"fr": "Adminer n'est pas installé.", "en": "Adminer is not installed."},
    "label_storage": {"fr": "Stockage", "en": "Storage"},
    "label_unavailable": {"fr": "Indisponible", "en": "Unavailable"},
    "label_system_services": {"fr": "Services système", "en": "System services"},
    "down_of_total": {"fr": "en arrêt sur {total}", "en": "down out of {total}"},
    "error_and_warning_count": {"fr": "erreur{es}, {warnings} avertissement{ws}", "en": "error{es}, {warnings} warning{ws}"},
    "label_failed_units": {"fr": "Unités en échec", "en": "Failed units"},
    "failed_units_list": {"fr": "en échec : {list}", "en": "failed: {list}"},
    "word_failed": {"fr": "en échec", "en": "failed"},
    "label_last_backup": {"fr": "Dernière sauvegarde", "en": "Last backup"},
    "word_none": {"fr": "Aucune", "en": "None"},
    "apps_and_categories": {"fr": "{apps} app{aps}, {cats} {cat_word}", "en": "{apps} app{aps}, {cats} {cat_word}"},
    "system_category_singular": {"fr": "catégorie système", "en": "system category"},
    "system_category_plural": {"fr": "catégories système", "en": "system categories"},

    "err_cert_not_installed": {
        "fr": "Domaine ajouté, mais le certificat Let's Encrypt n'a pas pu être installé (DNS pas encore propagé ?) — un certificat auto-signé est utilisé en attendant.",
        "en": "Domain added, but the Let's Encrypt certificate could not be installed (DNS not propagated yet?) — a self-signed certificate is used in the meantime.",
    },
    "msg_domain_added": {"fr": "Domaine ajouté.", "en": "Domain added."},
    "err_local_domain_created_rewrite_failed": {
        "fr": "Domaine {domain} créé, mais la réécriture DNS AdGuard a échoué — à vérifier manuellement.",
        "en": "Domain {domain} created, but the AdGuard DNS rewrite failed — check manually.",
    },
    "msg_local_domain_created": {"fr": "Domaine local {domain} créé.", "en": "Local domain {domain} created."},
    "msg_local_domain_removed": {"fr": "Domaine local {domain} supprimé.", "en": "Local domain {domain} removed."},

    "search_installed_app_placeholder": {"fr": "Rechercher une application installée...", "en": "Search an installed application..."},
    "btn_install_an_app": {"fr": "Installer une application", "en": "Install an application"},
    "no_app_installed": {"fr": "Aucune app installée.", "en": "No app installed."},
    "no_app_matches_search": {"fr": "Aucune app ne correspond à la recherche.", "en": "No app matches the search."},
    "permissions_count": {"fr": "Permissions ({n})", "en": "Permissions ({n})"},
    "searching": {"fr": "Vérification…", "en": "Checking…"},

    "title_url_app_map": {"fr": "Correspondance URL ↔ app", "en": "URL ↔ app mapping"},
    "th_path": {"fr": "Chemin", "en": "Path"},
    "th_app": {"fr": "App", "en": "App"},
    "th_label": {"fr": "Étiquette", "en": "Label"},
    "th_domain": {"fr": "Domaine", "en": "Domain"},
    "no_app_on_web_domain": {"fr": "Aucune application installée sur un domaine web.", "en": "No application installed on a web domain."},
    "tab_by_domain": {"fr": "Par domaine", "en": "By domain"},
    "tab_by_app": {"fr": "Par app", "en": "By app"},

    "word_app_fallback": {"fr": "App", "en": "App"},
    "btn_understood": {"fr": "Compris", "en": "Understood"},
    "btn_open_app": {"fr": "Ouvrir l'app", "en": "Open the app"},
    "label_installed_version": {"fr": "Version installée :", "en": "Installed version:"},
    "label_available_version": {"fr": "Version disponible : {version}", "en": "Available version: {version}"},
    "pinned_channel_note": {
        "fr": "Épinglée sur le canal « {channel} » — {message}",
        "en": "Pinned to the \"{channel}\" channel — {message}",
    },
    "not_necessarily_stable": {"fr": "pas forcément stable.", "en": "not necessarily stable."},
    "read_before_upgrade": {"fr": "À lire avant de mettre à jour :", "en": "Read before upgrading:"},
    "btn_force_upgrade": {"fr": "Forcer la mise à jour", "en": "Force upgrade"},
    "checkbox_force_despite_requirements": {"fr": "Forcer malgré les prérequis non satisfaits", "en": "Force despite unmet requirements"},
    "h3_rename_label": {"fr": "Changer le libellé", "en": "Change label"},
    "label_new_label": {"fr": "Nouveau libellé", "en": "New label"},
    "btn_rename": {"fr": "Renommer", "en": "Rename"},
    "h3_raw_setting": {"fr": "Réglage brut (support à distance)", "en": "Raw setting (remote support)"},
    "raw_setting_desc": {
        "fr": "Lit ou modifie un réglage interne de l'app tel que stocké par Wappos — utile pour du support sans accès SSH. Les clés dépendent de chaque app (ex. {examples}).",
        "en": "Reads or changes an internal app setting as stored by Wappos — useful for support without SSH access. Keys depend on each app (e.g. {examples}).",
    },
    "label_setting_key": {"fr": "Clé de réglage", "en": "Setting key"},
    "btn_read": {"fr": "Lire", "en": "Read"},
    "value_undefined": {"fr": "non défini", "en": "undefined"},
    "confirm_modify_raw_setting": {
        "fr": "Modifier le réglage interne « {key} » de cette app ? Une valeur incorrecte peut casser son fonctionnement.",
        "en": "Change this app's internal setting \"{key}\"? An incorrect value can break its operation.",
    },
    "label_new_value": {"fr": "Nouvelle valeur", "en": "New value"},
    "btn_modify": {"fr": "Modifier", "en": "Change"},
    "confirm_delete_raw_setting": {
        "fr": "Supprimer le réglage interne « {key} » de cette app ? Une suppression incorrecte peut casser son fonctionnement.",
        "en": "Delete this app's internal setting \"{key}\"? An incorrect deletion can break its operation.",
    },
    "btn_delete_this_setting": {"fr": "Supprimer ce réglage", "en": "Delete this setting"},
    "confirm_uninstall_app": {"fr": "Voulez-vous vraiment désinstaller {label} ? Cette action est irréversible.", "en": "Do you really want to uninstall {label}? This action is irreversible."},
    "checkbox_purge_app_data": {"fr": "Supprimer aussi toutes les données de l'app", "en": "Also delete all of the app's data"},
    "btn_uninstall_app": {"fr": "Désinstaller {label}", "en": "Uninstall {label}"},
    "app_not_found": {"fr": "App introuvable ou inaccessible.", "en": "App not found or unreachable."},

    "title_catalog": {"fr": "Catalogue", "en": "Catalog"},
    "search_app_placeholder": {"fr": "Rechercher une app...", "en": "Search for an app..."},
    "quality_high_only": {"fr": "Apps de haute qualité seulement", "en": "High quality apps only"},
    "quality_decent_only": {"fr": "Apps de qualité correcte seulement", "en": "Decent quality apps only"},
    "quality_working_only": {"fr": "Apps fonctionnelles seulement", "en": "Working apps only"},
    "quality_all": {"fr": "Toutes les apps", "en": "All apps"},
    "btn_search": {"fr": "Rechercher", "en": "Search"},
    "btn_see_categories": {"fr": "Retour aux catégories", "en": "Back to categories"},
    "word_all": {"fr": "Tout", "en": "All"},
    "word_others": {"fr": "Autres", "en": "Others"},
    "high_quality_app_title": {"fr": "Application de haute qualité", "en": "High quality application"},
    "badge_state": {"fr": "état : {state}", "en": "status: {state}"},
    "badge_unmaintained": {"fr": "non maintenue", "en": "unmaintained"},
    "btn_install": {"fr": "Installer", "en": "Install"},
    "no_app_found": {"fr": "Aucune app trouvée.", "en": "No app found."},
    "no_app_found_for_search": {"fr": "Aucune app trouvée pour « {search} ».", "en": "No app found for \"{search}\"."},
    "h3_custom_install": {"fr": "Installation personnalisée", "en": "Custom installation"},
    "custom_install_desc": {"fr": "Installer depuis un dépôt git ou un chemin local, hors catalogue.", "en": "Install from a git repository or local path, outside the catalog."},

    "title_install_name": {"fr": "Installer {name}", "en": "Install {name}"},
    "h1_install_name": {"fr": "Installer {name}", "en": "Install {name}"},
    "label_version": {"fr": "Version {version}", "en": "Version {version}"},
    "h3_links": {"fr": "Liens", "en": "Links"},
    "label_license": {"fr": "Licence : {license}", "en": "License: {license}"},
    "link_official_website": {"fr": "Site officiel", "en": "Official website"},
    "link_admin_doc": {"fr": "Documentation d'administration", "en": "Admin documentation"},
    "link_user_doc": {"fr": "Documentation utilisateur", "en": "User documentation"},
    "link_official_code": {"fr": "Dépôt officiel de code", "en": "Official code repository"},
    "alternative_to": {"fr": "Alternative à : {names}", "en": "Alternative to: {names}"},
    "h3_unmet_requirements": {"fr": "Prérequis non satisfaits", "en": "Unmet requirements"},
    "blocking_requirements_note": {
        "fr": "Ces conditions bloquent l'installation même en forçant, tout comme le WebAdmin natif.",
        "en": "These conditions block installation even when forcing it, just like the native WebAdmin.",
    },
    "label_app_label": {"fr": "Libellé de l'app", "en": "App label"},
    "checkbox_force_insufficient_ram": {"fr": "Forcer l'installation malgré la RAM insuffisante", "en": "Force installation despite insufficient RAM"},
    "checkbox_all_domains": {"fr": "Rendre accessible sur tous les domaines", "en": "Make accessible on all domains"},
    "checkbox_all_domains_help": {
        "fr": "L'app reste installée sur le domaine choisi ci-dessus, mais sa tuile et son URL fonctionneront aussi sur vos autres domaines (actuels et futurs).",
        "en": "The app stays installed on the domain chosen above, but its tile and URL will also work on your other domains (current and future).",
    },
    "app_not_found_in_catalog": {"fr": "App introuvable dans le catalogue.", "en": "App not found in the catalog."},
    "h3_cross_domain": {"fr": "Domaines supplémentaires", "en": "Additional domains"},
    "cross_domain_help": {
        "fr": "Ajoute cette app sur d'autres domaines en plus de celui où elle est installée, avec la même URL et le même accès.",
        "en": "Makes this app also reachable on other domains besides the one it's installed on, with the same URL and access.",
    },
    "no_cross_domain_entry": {"fr": "Aucun domaine supplémentaire.", "en": "No additional domain."},
    "label_add_domain": {"fr": "Ajouter un domaine", "en": "Add a domain"},
    "btn_add_domain": {"fr": "Ajouter", "en": "Add"},
    "btn_remove_domain": {"fr": "Retirer", "en": "Remove"},
    "confirm_remove_cross_domain": {"fr": "Retirer {domain} des domaines supplémentaires de cette app ?", "en": "Remove {domain} from this app's additional domains?"},
    "err_domain_required": {"fr": "Un domaine doit être sélectionné.", "en": "A domain must be selected."},
    "msg_cross_domain_added": {"fr": "{domain} ajouté aux domaines supplémentaires.", "en": "{domain} added to additional domains."},
    "msg_cross_domain_removed": {"fr": "{domain} retiré des domaines supplémentaires.", "en": "{domain} removed from additional domains."},
    "address_available": {"fr": "Adresse disponible.", "en": "Address available."},
    "address_already_used": {"fr": "Adresse déjà utilisée par une autre app.", "en": "Address already used by another app."},

    "err_setting_key_empty": {"fr": "La clé de réglage ne peut pas être vide.", "en": "The setting key cannot be empty."},
    "msg_setting_updated": {"fr": "Réglage « {key} » mis à jour.", "en": "Setting \"{key}\" updated."},
    "msg_setting_deleted": {"fr": "Réglage « {key} » supprimé.", "en": "Setting \"{key}\" deleted."},
    "msg_upgrade_started": {"fr": "Mise à jour lancée.", "en": "Update started."},
    "err_domain_path_required": {"fr": "Domaine et chemin requis.", "en": "Domain and path required."},
    "msg_url_changed": {"fr": "URL modifiée.", "en": "URL changed."},
    "err_label_empty": {"fr": "Le libellé ne peut pas être vide.", "en": "The label cannot be empty."},
    "msg_label_changed": {"fr": "Libellé modifié.", "en": "Label changed."},
    "msg_app_uninstalled": {"fr": "App désinstallée.", "en": "App uninstalled."},
    "msg_app_installed": {"fr": "« {label} » installée.", "en": "\"{label}\" installed."},

    "no_service": {"fr": "Aucun service.", "en": "No service."},
    "since_word": {"fr": "depuis {value}", "en": "since {value}"},
    "not_installed_on_server": {"fr": "non installé sur ce serveur", "en": "not installed on this server"},
    "title_service_name": {"fr": "{name} — Services", "en": "{name} — Services"},
    "nav_services": {"fr": "Services", "en": "Services"},
    "confirm_restart_service": {"fr": "Voulez-vous vraiment redémarrer {name} ?", "en": "Do you really want to restart {name}?"},
    "confirm_stop_service": {"fr": "Voulez-vous vraiment arrêter {name} ?", "en": "Do you really want to stop {name}?"},
    "confirm_start_service": {"fr": "Voulez-vous vraiment démarrer {name} ?", "en": "Do you really want to start {name}?"},
    "label_status": {"fr": "Statut", "en": "Status"},
    "label_start_on_boot": {"fr": "Lancement au démarrage", "en": "Start on boot"},
    "value_enabled": {"fr": "Activé", "en": "Enabled"},
    "value_disabled": {"fr": "Désactivé", "en": "Disabled"},
    "confirm_disable_critical_service": {
        "fr": "Voulez-vous vraiment désactiver {name} au démarrage ? C'est un service critique — le serveur pourrait ne plus redémarrer correctement.",
        "en": "Do you really want to disable {name} at boot? This is a critical service — the server might not restart correctly.",
    },
    "confirm_disable_service": {"fr": "Voulez-vous vraiment désactiver {name} au démarrage ?", "en": "Do you really want to disable {name} at boot?"},
    "btn_disable": {"fr": "Désactiver", "en": "Disable"},
    "btn_enable": {"fr": "Activer", "en": "Enable"},
    "label_configuration": {"fr": "Configuration", "en": "Configuration"},
    "config_valid": {"fr": "Valide", "en": "Valid"},
    "config_broken": {"fr": "Cassée", "en": "Broken"},
    "config_unknown": {"fr": "Inconnue", "en": "Unknown"},
    "h2_logs": {"fr": "Journaux", "en": "Logs"},
    "label_lines_per_log": {"fr": "Lignes par journal :", "en": "Lines per log:"},

    "title_failed_units": {"fr": "Unités en échec", "en": "Failed units"},
    "err_cannot_list_failed_units": {"fr": "Impossible de lister les unités en échec.", "en": "Unable to list failed units."},
    "no_failed_unit": {"fr": "Aucune unité en échec.", "en": "No failed unit."},

    "err_critical_service_confirm_required": {"fr": "Confirmation requise : {name} est un service critique.", "en": "Confirmation required: {name} is a critical service."},
    "action_word_start": {"fr": "démarré", "en": "started"},
    "action_word_stop": {"fr": "arrêté", "en": "stopped"},
    "action_word_restart": {"fr": "redémarré", "en": "restarted"},
    "action_word_enable": {"fr": "activé au démarrage", "en": "enabled at boot"},
    "action_word_disable": {"fr": "désactivé au démarrage", "en": "disabled at boot"},
    "msg_service_action": {"fr": "Service {name} {action}.", "en": "Service {name} {action}."},

    "log_cat_application": {"fr": "Application", "en": "Application"},
    "log_cat_backup": {"fr": "Sauvegarde", "en": "Backup"},
    "log_cat_diagnosis": {"fr": "Diagnostic", "en": "Diagnosis"},
    "log_cat_service": {"fr": "Service", "en": "Service"},
    "log_cat_domain": {"fr": "Domaine", "en": "Domain"},
    "log_cat_dyndns": {"fr": "DynDNS", "en": "DynDNS"},
    "log_cat_user": {"fr": "Utilisateur", "en": "User"},
    "log_cat_group": {"fr": "Groupe", "en": "Group"},
    "log_cat_settings": {"fr": "Réglages", "en": "Settings"},
    "log_cat_system": {"fr": "Système", "en": "System"},
    "log_cat_configuration": {"fr": "Configuration", "en": "Configuration"},
    "log_cat_other": {"fr": "Autre", "en": "Other"},

    "nav_settings": {"fr": "Réglages", "en": "Settings"},
    "nav_updates": {"fr": "Mises à jour", "en": "Updates"},
    "nav_firewall": {"fr": "Pare-feu", "en": "Firewall"},
    "nav_performance": {"fr": "Performances", "en": "Performance"},
    "nav_storage": {"fr": "Stockage", "en": "Storage"},
    "nav_logs": {"fr": "Journaux", "en": "Logs"},
    "nav_security": {"fr": "Sécurité", "en": "Security"},
    "nav_app_map": {"fr": "Correspondance URL &harr; app", "en": "URL &harr; app mapping"},

    "title_storage": {"fr": "Stockage", "en": "Storage"},
    "h3_disk_usage": {"fr": "Occupation", "en": "Disk usage"},
    "h3_physical_disks": {"fr": "Disques physiques", "en": "Physical disks"},
    "storage_used_of_total": {"fr": "{used} utilisés sur {total} ({percent}%)", "en": "{used} used of {total} ({percent}%)"},
    "storage_free": {"fr": "{free} libres", "en": "{free} free"},
    "disk_status_sane_title": {"fr": "Ce périphérique est sain", "en": "This device is healthy"},
    "disk_status_critical_title": {"fr": "Cet appareil est dans un état critique", "en": "This device is in a critical state"},
    "disk_status_unknown_title": {"fr": "L'état de cet appareil est inconnu", "en": "This device's state is unknown"},
    "disk_usb_title": {"fr": "Cet appareil est connecté en USB", "en": "This device is connected via USB"},
    "disk_removable_title": {"fr": "Cet appareil est éjectable", "en": "This device is removable"},
    "disk_label_device": {"fr": "Périphérique", "en": "Device"},
    "disk_label_serial": {"fr": "Numéro de série", "en": "Serial number"},
    "disk_serial_unknown": {"fr": "Inconnu", "en": "Unknown"},
    "disk_label_size": {"fr": "Taille", "en": "Size"},
    "disk_label_type": {"fr": "Type", "en": "Type"},
    "smart_global_passed": {"fr": "Test SMART global : réussi", "en": "Overall SMART test: passed"},
    "smart_global_failed": {"fr": "Test SMART global : échoué", "en": "Overall SMART test: failed"},
    "smart_global_unavailable": {"fr": "Test SMART global : indisponible", "en": "Overall SMART test: unavailable"},
    "smart_fact_temperature": {"fr": "Température : {value} °C", "en": "Temperature: {value} °C"},
    "smart_fact_power_on_hours": {"fr": "Heures de fonctionnement : {value} h", "en": "Power-on hours: {value} h"},
    "smart_fact_power_cycle_count": {"fr": "Cycles d'alimentation : {value}", "en": "Power cycle count: {value}"},
    "smart_fact_nvme_percentage_used": {"fr": "Usure NVMe : {value}%", "en": "NVMe wear: {value}%"},
    "smart_fact_nvme_media_errors": {"fr": "Erreurs média NVMe : {value}", "en": "NVMe media errors: {value}"},
    "smart_fact_nvme_unsafe_shutdowns": {"fr": "Arrêts non propres : {value}", "en": "Unsafe shutdowns: {value}"},
    "smart_attr_table_id": {"fr": "ID", "en": "ID"},
    "smart_attr_table_name": {"fr": "Attribut", "en": "Attribute"},
    "smart_attr_table_value": {"fr": "Valeur", "en": "Value"},
    "smart_attr_table_worst": {"fr": "Pire", "en": "Worst"},
    "smart_attr_table_threshold": {"fr": "Seuil", "en": "Threshold"},
    "smart_attr_table_raw": {"fr": "Brut", "en": "Raw"},
    "smart_unavailable_on_disk": {"fr": "SMART indisponible sur ce disque", "en": "SMART unavailable on this disk"},
    "err_no_disk_found": {"fr": "Aucun disque trouvé sur le système. Peut-être êtes-vous dans un contexte particulier, tel qu'un conteneur LXC ?", "en": "No disk found on the system. You might be in a special context, such as an LXC container?"},

    "title_performance": {"fr": "Performances", "en": "Performance"},
    "err_prometheus_unavailable": {"fr": "Prometheus n'est pas accessible pour l'instant — vérifie que le service tourne et que l'identifiant de lecture ({name}) est bien configuré côté Prometheus.", "en": "Prometheus is not reachable right now — check that the service is running and that the read-only credential ({name}) is properly configured on the Prometheus side."},
    "perf_intro": {"fr": "Les 4 indicateurs qui comptent réellement pour surveiller une app, mesurés sur les 5 dernières minutes (graphiques : 6 dernières heures).", "en": "The 4 metrics that really matter for monitoring an app, measured over the last 5 minutes (charts: last 6 hours)."},
    "perf_label_req_rate": {"fr": "Requêtes / seconde", "en": "Requests / second"},
    "perf_label_error_rate": {"fr": "Taux d'erreur", "en": "Error rate"},
    "perf_label_p95": {"fr": "Temps de réponse (p95)", "en": "Response time (p95)"},
    "perf_label_memory": {"fr": "Mémoire", "en": "Memory"},
    "unit_mb": {"fr": "Mo", "en": "MB"},

    "title_not_found": {"fr": "Page introuvable", "en": "Page not found"},
    "not_found_text": {"fr": "Cette page n'existe pas ou plus.", "en": "This page does not exist, or no longer exists."},
    "btn_back_to_home": {"fr": "Retour à l'accueil", "en": "Back to home"},

    "title_migrations": {"fr": "Migrations", "en": "Migrations"},
    "migrations_intro": {"fr": "Les migrations système modifient en profondeur la configuration du serveur (montées de version majeures, restructuration de composants). Les migrations <strong>automatiques</strong> s'exécutent déjà seules lors d'une mise à jour système normale. Les migrations <strong>manuelles</strong> nécessitent une action explicite ici, après lecture de leur avertissement.", "en": "System migrations deeply change the server's configuration (major version upgrades, component restructuring). <strong>Automatic</strong> migrations already run on their own during a normal system update. <strong>Manual</strong> migrations require an explicit action here, after reading their warning."},
    "confirm_run_pending_migrations": {"fr": "Exécuter toutes les migrations automatiques en attente ? Les migrations manuelles doivent être lancées individuellement ci-dessous.", "en": "Run all pending automatic migrations? Manual migrations must be run individually below."},
    "btn_run_pending_migrations": {"fr": "Exécuter les migrations automatiques en attente", "en": "Run pending automatic migrations"},
    "migration_mode_manual": {"fr": "Manuelle", "en": "Manual"},
    "migration_mode_auto": {"fr": "Automatique", "en": "Automatic"},
    "confirm_run_migration_disclaimer": {"fr": "Exécuter la migration « {name} » ? Cette action peut être longue et modifier significativement le serveur.", "en": "Run the migration \"{name}\"? This action can take a long time and significantly change the server."},
    "label_accept_disclaimer": {"fr": "J'ai lu et j'accepte l'avertissement ci-dessus.", "en": "I have read and accept the warning above."},
    "btn_run_migration": {"fr": "Exécuter cette migration", "en": "Run this migration"},
    "confirm_run_migration": {"fr": "Exécuter la migration « {name} » ?", "en": "Run the migration \"{name}\"?"},
    "no_pending_migration": {"fr": "Aucune migration en attente.", "en": "No pending migration."},
    "migrations_already_done": {"fr": "Migrations déjà effectuées ({count})", "en": "Migrations already done ({count})"},

    "title_firewall": {"fr": "Pare-feu", "en": "Firewall"},
    "h3_ports_protocol": {"fr": "Ports {protocol}", "en": "{protocol} ports"},
    "th_port": {"fr": "Port", "en": "Port"},
    "th_open": {"fr": "Ouvrir", "en": "Open"},
    "th_upnp": {"fr": "UPnP", "en": "UPnP"},
    "confirm_close_port": {"fr": "Fermer le port {port}/{protocol} ?", "en": "Close port {port}/{protocol}?"},
    "aria_close_port": {"fr": "Fermer le port {port}", "en": "Close port {port}"},
    "confirm_open_port": {"fr": "Ouvrir le port {port}/{protocol} ?", "en": "Open port {port}/{protocol}?"},
    "aria_open_port": {"fr": "Ouvrir le port {port}", "en": "Open port {port}"},
    "aria_disable_upnp_port": {"fr": "Désactiver le transfert UPnP pour le port {port}", "en": "Disable UPnP forwarding for port {port}"},
    "aria_enable_upnp_port": {"fr": "Activer le transfert UPnP pour le port {port}", "en": "Enable UPnP forwarding for port {port}"},
    "title_upnp_requires_open": {"fr": "Le port doit être ouvert pour transférer via UPnP", "en": "The port must be open to forward via UPnP"},
    "no_port_registered": {"fr": "Aucun port {protocol} enregistré.", "en": "No {protocol} port registered."},
    "label_action": {"fr": "Action", "en": "Action"},
    "option_open": {"fr": "Ouvrir", "en": "Open"},
    "option_close": {"fr": "Fermer", "en": "Close"},
    "label_port": {"fr": "Port", "en": "Port"},
    "title_port_pattern": {"fr": "Un port (1-65535) ou une plage N-M", "en": "A port (1-65535) or a range N-M"},
    "label_protocol": {"fr": "Protocole", "en": "Protocol"},
    "label_comment": {"fr": "Commentaire", "en": "Comment"},
    "placeholder_comment_app_name": {"fr": "ex. nom de l'app", "en": "e.g. app name"},
    "label_also_forward_upnp": {"fr": "Transférer aussi ce port via UPnP", "en": "Also forward this port via UPnP"},
    "label_remove_upnp_only": {"fr": "Retirer seulement le transfert UPnP (sans fermer le port)", "en": "Remove only the UPnP forwarding (without closing the port)"},
    "upnp_status_text": {"fr": "L'UPnP est {state} — permet à Wappos de demander à votre routeur d'ouvrir automatiquement les ports transférés ci-dessus.", "en": "UPnP is {state} — lets Wappos ask your router to automatically open the ports forwarded above."},
    "upnp_state_enabled": {"fr": "activé", "en": "enabled"},
    "upnp_state_disabled": {"fr": "désactivé", "en": "disabled"},
    "confirm_toggle_upnp": {"fr": "Voulez-vous vraiment {action} l'UPnP ?", "en": "Do you really want to {action} UPnP?"},
    "upnp_action_disable": {"fr": "désactiver", "en": "disable"},
    "upnp_action_enable": {"fr": "activer", "en": "enable"},
    "err_port_empty": {"fr": "Le port ne peut pas être vide.", "en": "The port cannot be empty."},
    "err_port_invalid": {"fr": "Port invalide (attendu : un nombre ou une plage N-M).", "en": "Invalid port (expected: a number or a range N-M)."},
    "h3_domain_smtp_relay": {"fr": "Relais SMTP sortant de ce domaine", "en": "This domain's outgoing SMTP relay"},
    "domain_smtp_relay_help": {
        "fr": "Route les mails envoyés depuis ce domaine par un serveur relais externe (ex. votre propre compte SMTP2GO), au lieu de l'envoi direct du serveur.",
        "en": "Routes mail sent from this domain through an external relay server (e.g. your own SMTP2GO account), instead of the server's direct delivery.",
    },
    "label_relay_host": {"fr": "Hôte du relais", "en": "Relay host"},
    "label_relay_port": {"fr": "Port", "en": "Port"},
    "label_relay_user": {"fr": "Utilisateur", "en": "Username"},
    "label_relay_password": {"fr": "Mot de passe", "en": "Password"},
    "placeholder_relay_password_unchanged": {"fr": "laisser vide pour ne pas changer", "en": "leave blank to keep unchanged"},
    "no_domain_smtp_relay": {"fr": "Aucun relais configuré — envoi direct.", "en": "No relay configured — direct delivery."},
    "btn_save_relay": {"fr": "Enregistrer", "en": "Save"},
    "btn_remove_relay": {"fr": "Retirer le relais", "en": "Remove relay"},
    "confirm_remove_domain_smtp_relay": {"fr": "Retirer le relais SMTP de ce domaine et revenir à l'envoi direct ?", "en": "Remove this domain's SMTP relay and go back to direct delivery?"},
    "err_smtp_relay_fields_required": {"fr": "L'hôte et le port sont obligatoires.", "en": "Host and port are required."},
    "msg_smtp_relay_saved": {"fr": "Relais SMTP enregistré.", "en": "SMTP relay saved."},
    "msg_smtp_relay_removed": {"fr": "Relais SMTP retiré.", "en": "SMTP relay removed."},
    "err_port_out_of_range": {"fr": "Le port doit être compris entre 1 et 65535 (0 n'est pas autorisé).", "en": "The port must be between 1 and 65535 (0 is not allowed)."},
    "err_port_range_invalid": {"fr": "Plage de ports invalide (le premier port doit être inférieur au second).", "en": "Invalid port range (the first port must be lower than the second)."},
    "msg_port_opened": {"fr": "Port {port}/{protocol} ouvert.", "en": "Port {port}/{protocol} opened."},
    "msg_port_closed": {"fr": "Port {port}/{protocol} fermé.", "en": "Port {port}/{protocol} closed."},
    "confirm_action_port_protocol": {"fr": "%s le port %s/%s ?", "en": "%s port %s/%s?"},
    "msg_upnp_toggled": {"fr": "UPnP {state}.", "en": "UPnP {state}."},
    "msg_migration_executed": {"fr": "Migration {name} exécutée.", "en": "Migration {name} executed."},
    "msg_pending_migrations_executed": {"fr": "Migrations en attente exécutées.", "en": "Pending migrations executed."},

    "nav_tls_passthrough": {"fr": "TLS passthrough", "en": "TLS passthrough"},
    "title_tls_passthrough": {"fr": "TLS passthrough", "en": "TLS passthrough"},
    "tls_passthrough_info": {"fr": "Redirige le trafic TLS chiffré d'un domaine directement vers une autre machine, sans le déchiffrer sur ce serveur.", "en": "Routes a domain's encrypted TLS traffic directly to another machine, without decrypting it on this server."},
    "th_destination": {"fr": "Destination", "en": "Destination"},
    "label_destination": {"fr": "Destination (IP)", "en": "Destination (IP)"},
    "placeholder_destination_local": {"fr": "127.0.0.1", "en": "127.0.0.1"},
    "no_tls_passthrough_entry": {"fr": "Aucune entrée TLS passthrough.", "en": "No TLS passthrough entry."},
    "btn_add_entry": {"fr": "Ajouter", "en": "Add"},
    "btn_remove_entry": {"fr": "Retirer", "en": "Remove"},
    "confirm_remove_tls_passthrough_entry": {"fr": "Retirer l'entrée TLS passthrough pour {domain} ?", "en": "Remove the TLS passthrough entry for {domain}?"},
    "err_tls_passthrough_fields_required": {"fr": "Domaine, destination et port sont obligatoires.", "en": "Domain, destination and port are required."},
    "msg_tls_passthrough_entry_added": {"fr": "Entrée TLS passthrough ajoutée pour {domain}.", "en": "TLS passthrough entry added for {domain}."},
    "msg_tls_passthrough_entry_removed": {"fr": "Entrée TLS passthrough retirée pour {domain}.", "en": "TLS passthrough entry removed for {domain}."},

    "title_settings": {"fr": "Réglages", "en": "Settings"},
    "h3_appearance": {"fr": "Apparence", "en": "Appearance"},
    "label_theme": {"fr": "Thème", "en": "Theme"},
    "option_theme_system": {"fr": "Système", "en": "System"},
    "option_theme_light": {"fr": "Clair", "en": "Light"},
    "option_theme_dark": {"fr": "Sombre", "en": "Dark"},
    "summary_learn_more": {"fr": "En savoir plus", "en": "Learn more"},
    "help_security_experimental": {"fr": "Active des en-têtes de sécurité HTTP plus stricts sur toutes les applications servies par ce serveur (Content-Security-Policy renforcée, Permissions-Policy complétée) — recommandé par la Fondation Mozilla, mais peut casser des applications qui chargent des ressources externes ou utilisent certaines API du navigateur (caméra, capteurs, etc.). À tester après activation.", "en": "Enables stricter HTTP security headers on all applications served by this server (hardened Content-Security-Policy, extended Permissions-Policy) — recommended by the Mozilla Foundation, but may break applications that load external resources or use certain browser APIs (camera, sensors, etc.). Test after enabling."},
    "btn_apply_settings": {"fr": "Appliquer", "en": "Apply"},
    "err_no_settings_available": {"fr": "Aucun réglage disponible.", "en": "No settings available."},

    "help_select_multiple_ctrl": {"fr": "Ctrl/Cmd + clic pour sélectionner plusieurs valeurs.", "en": "Ctrl/Cmd + click to select multiple values."},
    "placeholder_tags_example": {"fr": "valeur1, valeur2, ...", "en": "value1, value2, ..."},
    "label_current_file": {"fr": "Fichier actuel : {filename}", "en": "Current file: {filename}"},
    "btn_delete": {"fr": "Supprimer", "en": "Delete"},
    "note_file_will_be_deleted": {"fr": "Ce fichier sera supprimé lors de l'enregistrement.", "en": "This file will be deleted when saved."},
    "label_replace_with_new_file": {"fr": "Remplacer par un nouveau fichier :", "en": "Replace with a new file:"},

    "err_invalid_upgrade_target": {"fr": "Cible de mise à jour invalide.", "en": "Invalid upgrade target."},
    "err_no_upgradable_app": {"fr": "Aucune app au statut « à jour disponible » à mettre à jour.", "en": "No app with an \"update available\" status to upgrade."},
    "err_apps_upgraded_before_failure": {"fr": "{count} app(s) mise(s) à jour avant l'échec sur « {name} » : {detail}", "en": "{count} app(s) upgraded before failure on \"{name}\": {detail}"},
    "msg_apps_upgraded": {"fr": "{count} app(s) mise(s) à jour.", "en": "{count} app(s) upgraded."},
    "msg_system_upgrade_done_api_restarting": {"fr": "Mise à jour système terminée — l'API Wappos redémarre, la page va se rafraîchir automatiquement.", "en": "System upgrade complete — the Wappos API is restarting, the page will refresh automatically."},
    "msg_upgrade_target_done": {"fr": "Mise à jour ({target}) terminée.", "en": "Upgrade ({target}) complete."},
    "regen_verb_preview": {"fr": "Aperçu", "en": "Preview"},
    "regen_verb_regeneration": {"fr": "Régénération", "en": "Regeneration"},
    "msg_regen_conf_done": {"fr": "{verb} de la configuration effectuée ({applied} appliquée(s), {pending} en attente).", "en": "Configuration {verb} done ({applied} applied, {pending} pending)."},

    "err_session_expired": {"fr": "Ta session a expiré, reconnecte-toi.", "en": "Your session has expired, please log in again."},
    "msg_docker_app_managed_here": {"fr": "{slug} est une app Docker Gate — gérée depuis cette page.", "en": "{slug} is a Docker Gate app — managed from this page."},
    "msg_app_config_applied": {"fr": "Configuration appliquée.", "en": "Configuration applied."},
    "msg_app_action_executed": {"fr": "Action exécutée.", "en": "Action executed."},
    "msg_diagnosis_relaunched": {"fr": "Diagnostic relancé.", "en": "Diagnosis relaunched."},
    "msg_diagnosis_item_ignored": {"fr": "Problème ignoré.", "en": "Issue ignored."},
    "err_no_matching_filter_removed": {"fr": "Aucun filtre correspondant trouvé — rien n'a été retiré.", "en": "No matching filter found — nothing was removed."},
    "msg_diagnosis_item_unignored": {"fr": "Problème réintégré au rapport.", "en": "Issue restored to the report."},
    "msg_log_shared": {"fr": "Journal partagé : {url}", "en": "Log shared: {url}"},
    "msg_settings_applied": {"fr": "Réglages appliqués.", "en": "Settings applied."},
    "err_invalid_archive_name": {"fr": "Nom d'archive invalide (lettres, chiffres, - et _ uniquement).", "en": "Invalid archive name (letters, digits, - and _ only)."},
    "msg_backup_created": {"fr": "Sauvegarde {name} créée.", "en": "Backup {name} created."},
    "err_select_item_to_restore": {"fr": "Sélectionnez au moins un élément à restaurer.", "en": "Select at least one item to restore."},
    "msg_restore_done": {"fr": "Restauration terminée.", "en": "Restore complete."},
    "msg_archive_deleted": {"fr": "Archive {name} supprimée.", "en": "Archive {name} deleted."},
    "msg_backup_schedule_saved": {"fr": "Réglages de sauvegarde automatique enregistrés.", "en": "Automatic backup settings saved."},
    "msg_retention_preview_none": {"fr": "Aperçu : aucune archive ne serait supprimée avec la politique actuelle.", "en": "Preview: no archive would be deleted with the current policy."},
    "msg_retention_preview_some": {"fr": "Aperçu : {count} archive(s) seraient supprimées avec la politique actuelle — {names}", "en": "Preview: {count} archive(s) would be deleted with the current policy — {names}"},
    "msg_update_list_refreshed": {"fr": "Liste des mises à jour rafraîchie.", "en": "Update list refreshed."},
    "err_no_yunohost_app_associated": {"fr": "Aucune app YunoHost associée.", "en": "No associated YunoHost app."},
    "err_domain_and_path_required": {"fr": "Domaine et chemin requis.", "en": "Domain and path required."},
    "msg_app_uninstalled_named": {"fr": "App {slug} supprimée.", "en": "App {slug} removed."},
    "err_unexpected": {"fr": "Erreur inattendue : {detail}", "en": "Unexpected error: {detail}"},
    "msg_container_removed": {"fr": "Conteneur {name} supprimé.", "en": "Container {name} removed."},
    "msg_volume_removed": {"fr": "Volume {name} supprimé.", "en": "Volume {name} removed."},
    "msg_network_removed": {"fr": "Réseau {name} supprimé.", "en": "Network {name} removed."},
    "msg_images_pruned": {"fr": "Images nettoyées, {freed_mb} Mo libérés.", "en": "Images cleaned up, {freed_mb} MB freed."},
    "msg_docker_ce_uninstalled": {"fr": "Docker CE désinstallé.", "en": "Docker CE uninstalled."},
    "msg_docker_ce_uninstalled_with_warnings": {"fr": "Docker CE désinstallé, avec avertissements (voir journaux).", "en": "Docker CE uninstalled, with warnings (see logs)."},

    "err_action_failed_api_refused": {"fr": "L'action a échoué (l'API Wappos a refusé la requête).", "en": "The action failed (the Wappos API refused the request)."},
    "errcode_user_already_exists": {"fr": "Cet identifiant existe déjà.", "en": "This username already exists."},
    "errcode_user_unknown": {"fr": "Utilisateur inconnu.", "en": "Unknown user."},
    "errcode_user_cannot_delete_last_admin": {"fr": "Impossible de supprimer le dernier administrateur.", "en": "Cannot delete the last administrator."},
    "errcode_invalid_password": {"fr": "Mot de passe invalide (trop faible ou incompatible).", "en": "Invalid password (too weak or incompatible)."},
    "errcode_group_unknown": {"fr": "Groupe inconnu.", "en": "Unknown group."},
    "errcode_permission_protected": {"fr": "Cette permission est protégée — les visiteurs ne peuvent pas y être ajoutés directement.", "en": "This permission is protected — visitors cannot be added to it directly."},
    "errcode_permission_require_account": {"fr": "Ce type de permission nécessite un compte (pas accessible aux visiteurs).", "en": "This permission type requires an account (not accessible to visitors)."},
    "errcode_permission_cant_add_to_all_users": {"fr": "Impossible d'ajouter tous les utilisateurs à cette permission.", "en": "Cannot add all users to this permission."},
    "errcode_diagnosis_unknown_categories": {"fr": "Catégorie de diagnostic inconnue.", "en": "Unknown diagnosis category."},
    "errcode_group_already_exist": {"fr": "Ce groupe existe déjà.", "en": "This group already exists."},
    "errcode_group_cannot_be_deleted": {"fr": "Ce groupe ne peut pas être supprimé.", "en": "This group cannot be deleted."},
    "errcode_group_cannot_edit_all_users": {"fr": "Le groupe 'Tous les comptes' ne peut pas être modifié directement.", "en": "The 'All users' group cannot be edited directly."},
    "errcode_group_cannot_edit_visitors": {"fr": "Le groupe 'Visiteurs' ne peut pas être modifié directement.", "en": "The 'Visitors' group cannot be edited directly."},
    "errcode_group_cannot_edit_primary_group": {"fr": "Ce groupe personnel ne peut pas être modifié directement.", "en": "This personal group cannot be edited directly."},
    "errcode_group_cannot_remove_last_admin": {"fr": "Impossible de retirer le dernier administrateur.", "en": "Cannot remove the last administrator."},
    "errcode_mail_alias_remove_failed": {"fr": "Échec de la suppression de l'alias mail.", "en": "Failed to remove the mail alias."},
    "errcode_user_import_missing_columns": {"fr": "Colonnes manquantes dans le fichier CSV.", "en": "Missing columns in the CSV file."},
    "errcode_user_import_bad_line": {"fr": "Ligne invalide dans le fichier CSV.", "en": "Invalid line in the CSV file."},
    "errcode_service_unknown": {"fr": "Service inconnu.", "en": "Unknown service."},
    "errcode_service_start_failed": {"fr": "Échec du démarrage du service.", "en": "Failed to start the service."},
    "errcode_service_stop_failed": {"fr": "Échec de l'arrêt du service.", "en": "Failed to stop the service."},
    "errcode_service_restart_failed": {"fr": "Échec du redémarrage du service.", "en": "Failed to restart the service."},
    "errcode_service_enable_failed": {"fr": "Échec de l'activation du service au démarrage.", "en": "Failed to enable the service at boot."},
    "errcode_service_disable_failed": {"fr": "Échec de la désactivation du service au démarrage.", "en": "Failed to disable the service at boot."},
    "errcode_upnp_port_open_failed": {"fr": "Échec de l'ouverture du port via UPnP (routeur non compatible ou UPnP désactivé dessus).", "en": "Failed to open the port via UPnP (incompatible router or UPnP disabled on it)."},
    "errcode_nftables_unavailable": {"fr": "nftables n'est pas disponible sur ce serveur.", "en": "nftables is not available on this server."},
    "errcode_app_unknown": {"fr": "App inconnue.", "en": "Unknown app."},
    "errcode_app_already_installed": {"fr": "Cette app est déjà installée.", "en": "This app is already installed."},
    "errcode_app_install_failed": {"fr": "L'installation a échoué.", "en": "The installation failed."},
    "errcode_app_removed": {"fr": "Cette app n'est plus installée.", "en": "This app is no longer installed."},
    "errcode_app_change_url_no_script": {"fr": "Cette app ne supporte pas le changement d'URL.", "en": "This app does not support changing its URL."},
    "errcode_app_change_url_identical_domains": {"fr": "Le domaine et le chemin sont identiques, rien à changer.", "en": "The domain and path are identical, nothing to change."},
    "errcode_app_upgrade_url_required": {"fr": "Cette app doit être mise à jour manuellement (aucune source connue dans le catalogue).", "en": "This app must be upgraded manually (no known source in the catalog)."},
    "errcode_app_upgrade_app_already_up_to_date": {"fr": "Cette app est déjà à jour.", "en": "This app is already up to date."},
    "errcode_app_action_broken_parsing": {"fr": "Les arguments fournis n'ont pas pu être interprétés.", "en": "The provided arguments could not be parsed."},
    "errcode_app_config_unable_to_apply": {"fr": "La configuration n'a pas pu être appliquée.", "en": "The configuration could not be applied."},
    "errcode_domain_unknown": {"fr": "Domaine inconnu.", "en": "Unknown domain."},
    "errcode_certmanager_domain_cert_not_selfsigned": {"fr": "Ce domaine a déjà un certificat valide (non auto-signé) — utilisez « forcer » pour le remplacer.", "en": "This domain already has a valid certificate (not self-signed) — use \"force\" to replace it."},
    "errcode_certmanager_attempt_to_replace_valid_cert": {"fr": "Ce domaine a déjà un certificat valide — utilisez « forcer » pour le remplacer.", "en": "This domain already has a valid certificate — use \"force\" to replace it."},
    "errcode_certmanager_attempt_to_renew_valid_cert": {"fr": "Ce certificat est encore valide plus de 15 jours — utilisez « forcer » pour le renouveler quand même.", "en": "This certificate is still valid for more than 15 days — use \"force\" to renew it anyway."},
    "errcode_certmanager_attempt_to_renew_nonLE_cert": {"fr": "Ce domaine n'a pas de certificat Let's Encrypt à renouveler.", "en": "This domain has no Let's Encrypt certificate to renew."},
    "errcode_certmanager_acme_not_configured_for_domain": {"fr": "Le défi ACME n'est pas configuré pour ce domaine (vérifiez la config DNS/nginx).", "en": "The ACME challenge is not configured for this domain (check the DNS/nginx config)."},
    "errcode_certmanager_domain_not_diagnosed_yet": {"fr": "Ce domaine n'a pas encore été diagnostiqué — lancez d'abord un diagnostic complet.", "en": "This domain has not been diagnosed yet — run a full diagnosis first."},
    "errcode_certmanager_domain_dns_ip_differs_from_public_ip": {"fr": "L'IP DNS de ce domaine ne correspond pas à l'IP publique du serveur — le certificat ne peut pas être installé.", "en": "This domain's DNS IP does not match the server's public IP — the certificate cannot be installed."},
    "errcode_certmanager_cert_install_success": {"fr": "Certificat installé avec succès.", "en": "Certificate installed successfully."},
    "errcode_main_domain_change_failed": {"fr": "Le changement de domaine principal a échoué.", "en": "Changing the main domain failed."},
    "errcode_domain_exists": {"fr": "Ce domaine existe déjà.", "en": "This domain already exists."},
    "errcode_domain_cannot_remove_main": {"fr": "Impossible de supprimer ce domaine : c'est le domaine principal. Définissez d'abord un autre domaine comme principal.", "en": "Cannot remove this domain: it is the main domain. Set another domain as main first."},
    "errcode_domain_cannot_remove_main_add_new_one": {"fr": "Impossible de supprimer ce domaine : c'est le domaine principal et le seul domaine existant. Ajoutez d'abord un autre domaine.", "en": "Cannot remove this domain: it is the main domain and the only existing domain. Add another domain first."},
    "errcode_domain_uninstall_app_first": {"fr": "Des apps sont encore installées sur ce domaine — cochez « Supprimer aussi les apps installées » ou désinstallez-les d'abord.", "en": "Apps are still installed on this domain — check \"Also remove installed apps\" or uninstall them first."},
    "errcode_domain_dns_push_managed_in_parent_domain": {"fr": "La configuration DNS automatique est gérée par le domaine parent — rien à faire ici.", "en": "Automatic DNS configuration is managed by the parent domain — nothing to do here."},
    "errcode_domain_dns_push_failed_to_authenticate": {"fr": "Échec de l'authentification auprès du registrar — vérifiez les identifiants API dans la configuration du domaine.", "en": "Authentication with the registrar failed — check the API credentials in the domain configuration."},
    "errcode_domain_registrar_is_not_configured": {"fr": "Le registrar n'est pas encore configuré pour ce domaine (identifiants API absents) — la configuration DNS automatique n'est pas disponible.", "en": "The registrar is not yet configured for this domain (missing API credentials) — automatic DNS configuration is not available."},
    "errcode_domain_dns_conf_special_use_tld": {"fr": "Ce domaine utilise un TLD à usage spécial (ex. .local/.test) — il n'est pas censé avoir de vrais enregistrements DNS.", "en": "This domain uses a special-use TLD (e.g. .local/.test) — it is not expected to have real DNS records."},

    "native_marker_registrar_supported": {"fr": "YunoHost a détecté automatiquement que ce domaine est géré par le registrar", "en": "YunoHost automatically detected that this domain is managed by the registrar"},
    "text_registrar_supported": {"fr": "Ce domaine semble être géré par le registrar **{registrar}**. Si vous le souhaitez, vous pouvez utiliser la configuration automatique de cette zone DNS, si vous lui fournissez les identifiants API appropriés. Vous pouvez également configurer manuellement vos enregistrements DNS", "en": "This domain appears to be managed by the registrar **{registrar}**. If you wish, you can use automatic configuration of this DNS zone by providing the appropriate API credentials. You can also configure your DNS records manually"},
    "native_marker_registrar_not_supported": {"fr": "n'a pas pu détecter automatiquement le bureau d'enregistrement gérant ce domaine", "en": "could not automatically detect the registrar managing this domain"},
    "text_registrar_not_supported": {"fr": "Wappos n'a pas pu détecter automatiquement le bureau d'enregistrement gérant ce domaine. Vous devez configurer manuellement vos enregistrements DNS.", "en": "Wappos could not automatically detect the registrar managing this domain. You must configure your DNS records manually."},

    "backup_status_complete": {"fr": "Complète", "en": "Complete"},
    "backup_status_incomplete": {"fr": "Incomplète", "en": "Incomplete"},
    "backup_status_error": {"fr": "Échec", "en": "Failed"},
    "backup_status_unknown": {"fr": "Inconnu", "en": "Unknown"},
    "backup_status_untracked": {"fr": "Non suivie (créée avant l'activation du suivi)", "en": "Not tracked (created before tracking was enabled)"},
    "backup_status_failed_targets_suffix": {"fr": " — {count} cible(s) en échec", "en": " — {count} failed target(s)"},

    "err_unknown_action": {"fr": "Action inconnue", "en": "Unknown action"},
    "action_word_started": {"fr": "démarrée", "en": "started"},
    "action_word_stopped": {"fr": "arrêtée", "en": "stopped"},
    "action_word_restarted": {"fr": "redémarrée", "en": "restarted"},
    "msg_docker_app_action_done": {"fr": "App {slug} {action}.", "en": "App {slug} {action}."},
    "step_check_parameters": {"fr": "Vérification des paramètres", "en": "Checking parameters"},
    "step_write_configuration": {"fr": "Écriture de la configuration", "en": "Writing configuration"},
    "step_fetch_new_image": {"fr": "Récupération de la nouvelle image", "en": "Fetching new image"},
    "step_restart_container": {"fr": "Redémarrage du conteneur", "en": "Restarting container"},

    "audit_label_orphan_containers": {"fr": "Conteneurs orphelins", "en": "Orphan containers"},
    "audit_label_orphan_volumes": {"fr": "Volumes orphelins", "en": "Orphan volumes"},
    "audit_label_orphan_networks": {"fr": "Réseaux orphelins", "en": "Orphan networks"},
    "audit_label_dangling_images": {"fr": "Images inutilisées", "en": "Unused images"},
    "audit_label_empty_domains": {"fr": "Domaines vides", "en": "Empty domains"},
    "audit_label_docker_ce_status": {"fr": "État de Docker CE", "en": "Docker CE status"},
    "audit_warning_unexpected": {"fr": "{label} : erreur inattendue ({detail})", "en": "{label}: unexpected error ({detail})"},
    "audit_warning_labeled": {"fr": "{label} : {detail}", "en": "{label}: {detail}"},

    "title_backups": {"fr": "Sauvegardes", "en": "Backups"},
    "h3_auto_backup_cleanup": {"fr": "Sauvegarde automatique et nettoyage", "en": "Automatic backup and cleanup"},
    "h3_backup_compression": {"fr": "Compression des sauvegardes", "en": "Backup compression"},
    "label_enable_daily_backup": {"fr": "Activer la sauvegarde automatique quotidienne", "en": "Enable automatic daily backup"},
    "label_frequency": {"fr": "Fréquence :", "en": "Frequency:"},
    "option_daily": {"fr": "Quotidienne", "en": "Daily"},
    "option_weekly": {"fr": "Hebdomadaire", "en": "Weekly"},
    "label_scope": {"fr": "Périmètre :", "en": "Scope:"},
    "option_full_system": {"fr": "Système complet", "en": "Full system"},
    "option_selected_apps": {"fr": "Apps sélectionnées", "en": "Selected apps"},
    "label_apps_concerned_if_scope_selected": {"fr": "Apps concernées si périmètre \"Apps sélectionnées\"", "en": "Apps concerned if scope is \"Selected apps\""},
    "label_enable_auto_cleanup": {"fr": "Activer le nettoyage automatique des anciennes sauvegardes", "en": "Enable automatic cleanup of old backups"},
    "label_policy": {"fr": "Politique :", "en": "Policy:"},
    "option_keep_last_n": {"fr": "Garder les N dernières", "en": "Keep the last N"},
    "option_keep_x_days": {"fr": "Garder X jours", "en": "Keep X days"},
    "unit_last_backups": {"fr": "dernières sauvegardes", "en": "last backups"},
    "unit_days": {"fr": "jours", "en": "days"},
    "btn_save_settings": {"fr": "Enregistrer les réglages", "en": "Save settings"},
    "btn_retention_preview": {"fr": "Aperçu du nettoyage (sans rien supprimer)", "en": "Cleanup preview (deletes nothing)"},
    "help_backup_schedule": {"fr": "La sauvegarde s'exécute chaque nuit à 2h si activée. Le nettoyage s'applique après chaque sauvegarde planifiée si activé.", "en": "The backup runs every night at 2am if enabled. Cleanup applies after each scheduled backup if enabled."},
    "h3_create_manual_backup": {"fr": "Créer une sauvegarde manuelle", "en": "Create a manual backup"},
    "placeholder_backup_name": {"fr": "nom (optionnel, auto-généré sinon)", "en": "name (optional, auto-generated otherwise)"},
    "title_backup_name_pattern": {"fr": "Lettres, chiffres, - et _ uniquement", "en": "Letters, digits, - and _ only"},
    "placeholder_backup_description": {"fr": "description (optionnel)", "en": "description (optional)"},
    "label_apps_to_include": {"fr": "Apps à inclure (aucune cochée = tout)", "en": "Apps to include (none checked = all)"},
    "btn_create_backup": {"fr": "Créer la sauvegarde", "en": "Create backup"},
    "help_backup_no_app_checked": {"fr": "Sans app cochée, la sauvegarde inclut tout le système et toutes les apps — peut prendre plusieurs minutes.", "en": "With no app checked, the backup includes the whole system and all apps — this may take several minutes."},
    "no_local_backup": {"fr": "Aucune sauvegarde locale.", "en": "No local backup."},

    "title_backup_named": {"fr": "Sauvegarde — {name}", "en": "Backup — {name}"},
    "h3_information": {"fr": "Informations", "en": "Information"},
    "th_created_on": {"fr": "Créée le", "en": "Created on"},
    "th_description": {"fr": "Description", "en": "Description"},
    "th_size": {"fr": "Taille", "en": "Size"},
    "th_included_apps": {"fr": "Apps incluses", "en": "Included apps"},
    "th_included_system_components": {"fr": "Composants système inclus", "en": "Included system components"},
    "btn_download": {"fr": "Télécharger", "en": "Download"},
    "h3_restore": {"fr": "Restaurer", "en": "Restore"},
    "help_restore_destructive": {"fr": "Restaure cette archive sur le serveur — peut écraser des données existantes (comptes, apps, configuration système déjà présents). Action destructrice.", "en": "Restores this archive on the server — may overwrite existing data (accounts, apps, system configuration already present). Destructive action."},
    "confirm_restore_backup": {"fr": "Restaurer la sauvegarde {name} ? Cette action peut écraser des données existantes.", "en": "Restore the backup {name}? This action may overwrite existing data."},
    "alert_type_exact_name_to_restore": {"fr": "Pour restaurer cette sauvegarde, tape exactement « {name} » dans le champ prévu.", "en": "To restore this backup, type exactly \"{name}\" in the field provided."},
    "label_apps_to_restore": {"fr": "Apps à restaurer", "en": "Apps to restore"},
    "label_system_parts_to_restore": {"fr": "Parties système à restaurer", "en": "System parts to restore"},
    "label_type_name_to_confirm": {"fr": "Tapez « {name} » pour confirmer", "en": "Type \"{name}\" to confirm"},
    "btn_restore": {"fr": "Restaurer", "en": "Restore"},
    "confirm_delete_archive": {"fr": "Supprimer définitivement l'archive {name} ? Cette action est irréversible.", "en": "Permanently delete the archive {name}? This action is irreversible."},
    "btn_delete_this_archive": {"fr": "Supprimer cette archive", "en": "Delete this archive"},
    "value_dash": {"fr": "—", "en": "—"},

    "title_diagnosis": {"fr": "Diagnostic", "en": "Diagnosis"},
    "diagnosis_intro_with_reports": {"fr": "La fonctionnalité de diagnostic va tenter de trouver certains problèmes communs sur différents aspects de votre serveur pour être sûr que tout fonctionne normalement. Le diagnostic sera également effectué deux fois par jour et enverra un courriel au compte administrateur si des erreurs sont détectées. À noter que certains tests ne seront pas montrés si vous n'utilisez pas certaines fonctions spécifiques (par exemple l'e-mail) ou s'ils échouent à cause d'une configuration trop complexe. Dans ce cas, et si vous savez ce que vous avez modifié, vous pouvez ignorer les problèmes et les avertissements correspondantes.", "en": "The diagnosis feature will try to find some common problems across different aspects of your server to make sure everything works normally. Diagnosis will also run twice a day and send an email to the administrator account if errors are detected. Note that some tests will not be shown if you do not use certain specific features (e.g. email) or if they fail because of an overly complex configuration. In that case, and if you know what you changed, you can ignore the corresponding issues and warnings."},
    "diagnosis_intro_no_reports": {"fr": "La fonctionnalité de diagnostic va tenter de trouver certains problèmes communs sur différents aspects de votre serveur pour être sûr que tout fonctionne normalement. Merci de ne pas paniquer si vous voyez une multitude d'erreurs après avoir configuré votre serveur : la fonctionnalité est précisément prévue pour les identifier et vous aider à les résoudre. Le diagnostic sera également effectué deux fois par jour et enverra un courriel au compte administrateur si des erreurs sont détectées.", "en": "The diagnosis feature will try to find some common problems across different aspects of your server to make sure everything works normally. Please do not panic if you see a multitude of errors after setting up your server: the feature is precisely designed to identify them and help you fix them. Diagnosis will also run twice a day and send an email to the administrator account if errors are detected."},
    "help_diagnosis_cache_valid": {"fr": "Les catégories dont le cache est encore valide ne seront pas revérifiées — utilisez « Relancer le diagnostic » sur une catégorie précise pour forcer une vérification immédiate.", "en": "Categories whose cache is still valid will not be re-checked — use \"Rerun diagnosis\" on a specific category to force an immediate check."},
    "btn_run_never_run_category": {"fr": "Lancer cette catégorie (jamais exécutée)", "en": "Run this category (never run)"},
    "btn_run_full_diagnosis": {"fr": "Lancer un diagnostic complet", "en": "Run a full diagnosis"},
    "btn_start_initial_diagnosis": {"fr": "Démarrer le diagnostic initial", "en": "Start the initial diagnosis"},
    "title_run_diagnosis": {"fr": "Exécuter le diagnostic", "en": "Run diagnosis"},
    "text_server_processing": {"fr": "Le serveur traite l'action... (jusqu'à 2 minutes)", "en": "The server is processing the action... (up to 2 minutes)"},
    "diag_all_ok": {"fr": "Tout est OK !", "en": "Everything is OK!"},
    "diag_n_problems": {"fr": "{count} problème{plural}", "en": "{count} problem{plural}"},
    "diag_n_warnings": {"fr": "{count} avertissement{plural}", "en": "{count} warning{plural}"},
    "diag_n_ignored": {"fr": "{count} ignoré{plural}", "en": "{count} ignored{plural}"},
    "label_last_run": {"fr": "Dernière exécution : {value}", "en": "Last run: {value}"},
    "btn_rerun_diagnosis": {"fr": "Relancer le diagnostic", "en": "Rerun diagnosis"},
    "btn_unignore": {"fr": "Ne plus ignorer", "en": "Unignore"},
    "btn_ignore": {"fr": "Ignorer", "en": "Ignore"},
    "btn_details": {"fr": "Détails", "en": "Details"},
    "err_api_unreachable_retry": {"fr": "Impossible de contacter l'API Wappos — réessayez.", "en": "Could not reach the Wappos API — please retry."},
    "unknown_date": {"fr": "Date inconnue", "en": "Unknown date"},

    "title_logs": {"fr": "Journaux", "en": "Logs"},
    "logs_intro": {"fr": "Regroupe par jour les opérations réellement journalisées par Wappos (apps, sauvegardes, services, diagnostic, domaines, utilisateurs, réglages, système). Les mises à jour d'apps ne sont pas journalisées nativement et n'apparaissent donc pas ici.", "en": "Groups by day the operations actually logged by Wappos (apps, backups, services, diagnosis, domains, users, settings, system). App updates are not natively logged and therefore do not appear here."},
    "placeholder_search_logs": {"fr": "Rechercher dans les journaux...", "en": "Search the logs..."},
    "no_operation_recorded": {"fr": "Aucune opération enregistrée.", "en": "No operation recorded."},
    "no_result": {"fr": "Aucun résultat.", "en": "No result."},

    "title_log_named": {"fr": "{description} — Journaux", "en": "{description} — Logs"},
    "th_path_generic": {"fr": "Chemin", "en": "Path"},
    "th_start": {"fr": "Début", "en": "Start"},
    "log_status_ok": {"fr": "Réussi", "en": "Succeeded"},
    "log_status_failed": {"fr": "Échoué", "en": "Failed"},
    "th_end": {"fr": "Fin", "en": "End"},
    "th_suboperations": {"fr": "Sous-opérations", "en": "Sub-operations"},
    "err_operation_failed_help": {"fr": "L'opération a échoué ! Vous pouvez essayer de demander de l'aide à la communauté Wappos.", "en": "The operation failed! You can try asking the Wappos community for help."},
    "h2_log": {"fr": "Journal", "en": "Log"},
    "confirm_share_log": {"fr": "Ce journal sera envoyé a un service de partage externe pour obtenir un lien partageable. Continuer ?", "en": "This log will be sent to an external sharing service to get a shareable link. Continue?"},
    "btn_share_online": {"fr": "Partager en ligne", "en": "Share online"},
    "btn_show_more_lines": {"fr": "Afficher plus de lignes", "en": "Show more lines"},

    "dg_err_docker_daemon_unreachable": {"fr": "Impossible de contacter le démon Docker — vérifiez qu'il est installé et démarré ({detail}).", "en": "Could not reach the Docker daemon — check that it is installed and running ({detail})."},
    "dg_err_cpu_limit_invalid": {"fr": "Limite CPU invalide : « {value} » (attendu un nombre positif, ex. 0.5).", "en": "Invalid CPU limit: \"{value}\" (expected a positive number, e.g. 0.5)."},
    "dg_err_mem_limit_invalid": {"fr": "Limite mémoire invalide : « {value} » — attendu un nombre suivi de m (méga-octets) ou g (giga-octets), ex. 512m ou 1g.", "en": "Invalid memory limit: \"{value}\" — expected a number followed by m (megabytes) or g (gigabytes), e.g. 512m or 1g."},
    "dg_err_no_free_port": {"fr": "Aucun port libre disponible dans la plage 9100-9999.", "en": "No free port available in the 9100-9999 range."},
    "dg_step_check_parameters": {"fr": "Vérification des paramètres", "en": "Checking parameters"},
    "dg_step_select_port": {"fr": "Sélection du port", "en": "Selecting port"},
    "dg_step_create_domain": {"fr": "Création du domaine", "en": "Creating domain"},
    "dg_step_dns_diagnosis": {"fr": "Diagnostic DNS", "en": "DNS diagnosis"},
    "dg_step_web_diagnosis": {"fr": "Diagnostic Web", "en": "Web diagnosis"},
    "dg_step_get_certificate": {"fr": "Obtention du certificat", "en": "Getting certificate"},
    "dg_step_check_certificate": {"fr": "Vérification du certificat", "en": "Checking certificate"},
    "dg_step_write_configuration": {"fr": "Écriture de la configuration", "en": "Writing configuration"},
    "dg_step_start_container": {"fr": "Démarrage du conteneur", "en": "Starting container"},
    "dg_step_expose_app": {"fr": "Exposition de l'app", "en": "Exposing app"},
    "dg_step_restart_container": {"fr": "Redémarrage du conteneur", "en": "Restarting container"},
    "dg_step_check_connectivity": {"fr": "Vérification de la connexion", "en": "Checking connectivity"},
    "dg_warn_port_not_responding": {
        "fr": "Le conteneur a démarré mais ne répond pas sur le port {port} — vérifiez le port réel utilisé par cette application (voir sa documentation) depuis Modifier les paramètres.",
        "en": "The container started but is not responding on port {port} — check the actual port used by this application (see its documentation) from Edit parameters.",
    },
    "dg_warn_app_returns_error_status": {
        "fr": "L'application a démarré mais renvoie une erreur ({status}) à l'adresse choisie. Certaines applications ne supportent pas d'être installées sous un chemin (ex. /monapp) et ont besoin d'un sous-domaine dédié — réessayez avec cette option si le problème persiste.",
        "en": "The application started but returns an error ({status}) at the chosen address. Some applications do not support being installed under a path (e.g. /myapp) and need a dedicated subdomain instead — retry with that option if the problem persists.",
    },
    "dg_err_https_only": {"fr": "Seules les URL https:// sont acceptées.", "en": "Only https:// URLs are accepted."},
    "dg_err_url_fetch_failed": {"fr": "Impossible de récupérer l'URL ({detail}).", "en": "Could not fetch the URL ({detail})."},
    "dg_err_file_too_large": {"fr": "Fichier trop volumineux (>200 Ko).", "en": "File too large (>200 KB)."},
    "dg_err_image_pull_failed": {"fr": "Impossible de télécharger l'image « {image} » ({detail}).", "en": "Could not download the image \"{image}\" ({detail})."},
    "dg_err_not_docker_run": {"fr": "Ce texte ne ressemble pas à une commande « docker run ».", "en": "This text does not look like a \"docker run\" command."},
    "dg_err_command_parse_failed": {"fr": "Impossible d'analyser la commande ({detail}).", "en": "Could not parse the command ({detail})."},
    "dg_err_no_run_subcommand": {"fr": "Aucun sous-commande « run » trouvée.", "en": "No \"run\" subcommand found."},
    "dg_warn_multiple_published_ports": {"fr": "Plusieurs ports publiés — seul le premier a été retenu.", "en": "Multiple published ports — only the first was kept."},
    "dg_warn_multiple_mounted_volumes": {"fr": "Plusieurs volumes montés — seul le premier a été retenu.", "en": "Multiple mounted volumes — only the first was kept."},
    "dg_err_no_docker_image_found": {"fr": "Aucune image Docker trouvée dans cette commande.", "en": "No Docker image found in this command."},
    "dg_err_nothing_to_parse": {"fr": "Rien à analyser.", "en": "Nothing to parse."},
    "dg_err_unrecognized_format": {"fr": "Format non reconnu — collez une image, une commande « docker run » ou un docker-compose.yml.", "en": "Unrecognized format — paste an image, a \"docker run\" command, or a docker-compose.yml."},
    "dg_warn_env_file_unsupported": {"fr": "« env_file » n'est pas supporté — ajoutez les variables manuellement.", "en": "\"env_file\" is not supported — add the variables manually."},
    "dg_warn_multiple_declared_ports": {"fr": "Plusieurs ports déclarés — seul le premier a été retenu.", "en": "Multiple declared ports — only the first was kept."},
    "dg_warn_multiple_declared_volumes": {"fr": "Plusieurs volumes déclarés — seul le premier a été retenu.", "en": "Multiple declared volumes — only the first was kept."},
    "dg_err_compose_invalid": {"fr": "docker-compose.yml invalide ({detail}).", "en": "Invalid docker-compose.yml ({detail})."},
    "dg_err_compose_not_valid_content": {"fr": "Ce contenu ne ressemble pas à un docker-compose.yml valide.", "en": "This content does not look like a valid docker-compose.yml."},
    "dg_err_no_service_found": {"fr": "Aucun service trouvé dans ce docker-compose.yml.", "en": "No service found in this docker-compose.yml."},
    "dg_warn_unresolved_vars": {"fr": "Variables non résolues : {names}.", "en": "Unresolved variables: {names}."},
    "dg_err_unrecognized_service_format": {"fr": "Format de service non reconnu.", "en": "Unrecognized service format."},
    "dg_err_no_image_found_compose": {"fr": "Aucune image trouvée dans ce docker-compose.yml.", "en": "No image found in this docker-compose.yml."},
    "dg_warn_env_example_used": {"fr": "Fichier d'exemple d'environnement du projet utilisé pour compléter env_file.", "en": "The project's example environment file was used to fill in env_file."},
    "dg_warn_secrets_autogenerated": {"fr": "Secrets auto-générés : {names}.", "en": "Auto-generated secrets: {names}."},
    "dg_err_nothing_usable_in_compose": {"fr": "Rien d'exploitable n'a été trouvé dans ce docker-compose.yml.", "en": "Nothing usable was found in this docker-compose.yml."},
    "dg_err_invalid_line_no_equals": {"fr": "Ligne {line_num} invalide (pas de « = ») : {line}", "en": "Invalid line {line_num} (no \"=\"): {line}"},
    "dg_err_invalid_config_filename": {"fr": "Nom de fichier de configuration invalide : « {name} ».", "en": "Invalid configuration file name: \"{name}\"."},
    "dg_err_timeout_after": {"fr": "{message} (délai dépassé après {timeout}s).", "en": "{message} (timed out after {timeout}s)."},
    "dg_err_with_detail": {"fr": "{message} : {detail}", "en": "{message}: {detail}"},
    "dg_err_invalid_subdomain": {"fr": "Sous-domaine invalide.", "en": "Invalid subdomain."},
    "dg_err_missing_parent_domain": {"fr": "Domaine parent manquant.", "en": "Missing parent domain."},
    "dg_err_missing_domain": {"fr": "Domaine manquant.", "en": "Missing domain."},
    "dg_err_invalid_path": {"fr": "Chemin invalide.", "en": "Invalid path."},
    "dg_err_invalid_slug": {"fr": "Identifiant (slug) invalide — lettres minuscules, chiffres et tirets uniquement.", "en": "Invalid identifier (slug) — lowercase letters, digits and hyphens only."},
    "dg_err_slug_already_used": {"fr": "L'identifiant « {slug} » est déjà utilisé.", "en": "The identifier \"{slug}\" is already in use."},
    "dg_err_container_port_must_be_number": {"fr": "Le port du conteneur doit être un nombre.", "en": "The container port must be a number."},
    "dg_warn_dns_diagnosis_unverified": {"fr": "Le diagnostic DNS de {domain} n'a pas pu être vérifié.", "en": "The DNS diagnosis of {domain} could not be verified."},
    "dg_warn_web_diagnosis_unverified": {"fr": "Le diagnostic Web de {domain} n'a pas pu être vérifié.", "en": "The Web diagnosis of {domain} could not be verified."},
    "dg_warn_cert_check_failed": {"fr": "Impossible de vérifier le certificat de {domain} ({detail}).", "en": "Could not check the certificate of {domain} ({detail})."},
    "dg_warn_cert_not_letsencrypt": {"fr": "Le certificat de {domain} n'est pas Let's Encrypt (« {ca_type} »). Vérifiez la configuration DNS et le transfert TLS, puis relancez l'installation.", "en": "The certificate of {domain} is not Let's Encrypt (\"{ca_type}\"). Check the DNS configuration and TLS forwarding, then retry the installation."},
    "dg_err_invalid_config_file_path": {"fr": "Chemin de fichier de configuration invalide : « {path} ».", "en": "Invalid configuration file path: \"{path}\"."},
    "dg_err_write_config_failed": {"fr": "Impossible d'écrire la configuration ({detail}).", "en": "Could not write the configuration ({detail})."},
    "dg_err_invalid_configuration": {"fr": "Configuration invalide", "en": "Invalid configuration"},
    "dg_err_container_start_failed": {"fr": "Échec du démarrage du conteneur", "en": "Container start failed"},
    "dg_warn_logo_not_applied": {"fr": "Le logo de l'app n'a pas pu être appliqué ({detail}).", "en": "The app's logo could not be applied ({detail})."},
    "dg_err_unknown_app": {"fr": "App inconnue : {slug}", "en": "Unknown app: {slug}"},
    "dg_err_no_service_in_container_config": {"fr": "Aucun service trouvé dans la configuration du conteneur.", "en": "No service found in the container configuration."},
    "dg_err_compose_file_not_found": {"fr": "Fichier compose introuvable pour cette app — elle a peut-être été créée avant cette fonctionnalité.", "en": "Compose file not found for this app — it may have been created before this feature existed."},
    "dg_err_image_required": {"fr": "L'image Docker est obligatoire.", "en": "The Docker image is required."},
    "dg_err_container_update_failed": {"fr": "Échec de la mise à jour du conteneur", "en": "Container update failed"},
    "dg_warn_yunohost_exposure_removal_failed": {"fr": "Échec du retrait de l'exposition YunoHost : {detail}", "en": "Failed to remove YunoHost exposure: {detail}"},
    "dg_err_container_stop_failed": {"fr": "Échec de l'arrêt du conteneur", "en": "Container stop failed"},
    "dg_err_container_stop_failed_detail": {"fr": "Échec de l'arrêt du conteneur : {detail}", "en": "Container stop failed: {detail}"},
    "dg_warn_domain_removal_failed": {"fr": "Échec de la suppression du domaine : {detail}", "en": "Failed to remove domain: {detail}"},
    "dg_err_unknown_action": {"fr": "Action inconnue : {action}", "en": "Unknown action: {action}"},
    "dg_err_action_failed": {"fr": "Échec du {action}", "en": "{action} failed"},
    "dg_err_no_container_for_app": {"fr": "Aucun conteneur associé à cette app.", "en": "No container associated with this app."},
    "dg_err_container_not_found": {"fr": "Conteneur « {name} » introuvable.", "en": "Container \"{name}\" not found."},
    "dg_err_not_recognized_orphan_container": {"fr": "« {name} » n'est pas un conteneur orphelin reconnu.", "en": "\"{name}\" is not a recognized orphan container."},
    "dg_err_not_recognized_orphan_volume": {"fr": "« {name} » n'est pas un volume orphelin reconnu.", "en": "\"{name}\" is not a recognized orphan volume."},
    "dg_err_not_recognized_orphan_network": {"fr": "« {name} » n'est pas un réseau orphelin reconnu.", "en": "\"{name}\" is not a recognized orphan network."},
    "dg_err_docker_stop_failed": {"fr": "Échec de l'arrêt de Docker", "en": "Failed to stop Docker"},
    "dg_err_purge_packages_failed": {"fr": "Échec de la purge des paquets Docker", "en": "Failed to purge Docker packages"},
    "dg_err_autoremove_failed": {"fr": "Échec du nettoyage des paquets orphelins", "en": "Failed to clean up orphan packages"},
    "dg_err_remove_data_failed": {"fr": "Échec de la suppression des données Docker", "en": "Failed to remove Docker data"},
    "dg_err_remove_apt_repo_failed": {"fr": "Échec de la suppression du dépôt APT Docker", "en": "Failed to remove the Docker APT repository"},
    "dg_err_remove_docker_group_failed": {"fr": "Échec de la suppression du groupe docker", "en": "Failed to remove the docker group"},
    "dg_err_restart_app_failed": {"fr": "Échec du redémarrage de {slug}", "en": "Failed to restart {slug}"},
    "dg_err_ldap_relay_description": {"fr": "Relais TCP LDAP pour les conteneurs Docker Gate", "en": "LDAP TCP relay for Docker Gate containers"},
    "dg_err_install_socat_failed": {"fr": "Impossible d'installer socat", "en": "Could not install socat"},
    "dg_err_install_ldap_relay_failed": {"fr": "Impossible d'installer le service de relais LDAP", "en": "Could not install the LDAP relay service"},
    "dg_err_systemd_reload_failed": {"fr": "Échec du rechargement systemd", "en": "systemd reload failed"},
    "dg_err_ldap_relay_start_failed": {"fr": "Échec du démarrage du relais LDAP", "en": "Failed to start the LDAP relay"},
    "dg_err_tag_list_unavailable": {"fr": "Liste des versions non disponible pour ce registre — seul Docker Hub est supporté pour l'instant.", "en": "Version list unavailable for this registry — only Docker Hub is supported for now."},
    "dg_err_docker_hub_query_failed": {"fr": "Impossible d'interroger Docker Hub ({detail}).", "en": "Could not query Docker Hub ({detail})."},
    "dg_step_fetch_new_image": {"fr": "Récupération de la nouvelle image", "en": "Fetching new image"},
    "dg_err_image_download_failed": {"fr": "Échec du téléchargement de la nouvelle image", "en": "New image download failed"},

    "page_body_documentation_superadmin": {
        "fr": (
            "<h2>À propos de cette interface</h2>"
            "<p>Wappos Admin est l'interface d'administration technique de votre serveur Wappos, réservée aux comptes "
            "administrateurs. Elle s'appuie sur YunoHost, le système d'exploitation serveur qui gère réellement les comptes, "
            "les domaines, les certificats, les applications et les sauvegardes — cette interface ne fait qu'afficher et "
            "piloter ce que YunoHost fait déjà, sans jamais dupliquer sa logique de sécurité. Vous êtes connecté ici en tant "
            "que <strong>superadmin</strong> : vous avez accès à l'intégralité des fonctions décrites ci-dessous, sans "
            "restriction de domaine.</p>"
            "<p>Pour la documentation destinée aux utilisateurs finaux (portail d'applications, profil, mot de passe), "
            "consultez la page Documentation du portail (lien \"Administration\" présent dans son pied de page, dans "
            "l'autre sens).</p>"

            "<h2>Deux profils d'administrateur</h2>"
            "<p>Wappos distingue deux niveaux de compte administrateur :</p>"
            "<ul>"
            "<li><strong>Superadmin</strong> : membre du groupe système <code>admins</code>. Accès complet, sans "
            "restriction, à toutes les fonctions de cette interface — c'est vous.</li>"
            "<li><strong>Administrateur de domaine</strong> : membre du groupe <code>wappos_domain_admins</code>, jamais du "
            "groupe <code>admins</code>. Un administrateur de domaine ne voit et ne gère que ce qui appartient à son ou ses "
            "domaines : ses utilisateurs, ses applications, ses permissions, la configuration de son domaine. Il n'a accès à "
            "aucune fonction affectant le serveur dans son ensemble (voir la liste des exclusions plus bas).</li>"
            "</ul>"
            "<p>Un administrateur de domaine n'a pas de compte séparé technique : c'est un compte utilisateur ordinaire, "
            "simplement ajouté au groupe <code>wappos_domain_admins</code> puis associé à un ou plusieurs domaines. Voir la "
            "section \"Créer un administrateur de domaine\" plus bas pour la procédure complète.</p>"

            "<h2>Tableau de bord (Accueil)</h2>"
            "<p>La page d'accueil affiche un menu de raccourcis vers les grandes sections (Utilisateurs, Domaines, "
            "Applications, et pour vous uniquement : Groupes et permissions, Diagnostic, Sauvegardes, Système), ainsi qu'un "
            "tableau de bord synthétique réservé au superadmin : espace disque par volume, état des services système, "
            "résultat du dernier diagnostic, unités système en échec, date de la dernière sauvegarde, et nombre de mises à "
            "jour disponibles (applications et système). Chaque tuile du tableau de bord est cliquable et mène directement à "
            "la page correspondante pour plus de détail.</p>"

            "<h2>Utilisateurs</h2>"
            "<p>Liste tous les comptes du serveur. Pour vous, chaque compte administrateur affiche un badge (\"Superadmin\" "
            "ou \"Administrateur de domaine : &lt;domaine(s)&gt;\"), et la liste est triée pour faire remonter les comptes "
            "administrateurs en premier.</p>"
            "<h3>Créer un compte</h3>"
            "<p>Depuis le bas de la page Utilisateurs : identifiant, domaine de messagerie, nom complet et mot de passe "
            "initial. L'identifiant ne peut contenir que des minuscules, chiffres, points et tirets bas.</p>"
            "<h3>Modifier un compte</h3>"
            "<p>Cliquez sur un compte dans la liste pour arriver directement sur sa page d'édition : nom complet, adresse "
            "mail principale, alias et adresses de transfert, quota de messagerie, clés SSH publiques (ajout/suppression), "
            "réinitialisation du mot de passe, et suppression du compte (avec option de purger ses données).</p>"
            "<h3>Export / import CSV</h3>"
            "<p>L'export CSV télécharge la liste des comptes (filtrée à vos domaines si vous étiez administrateur de "
            "domaine — sans objet pour vous, superadmin, qui obtenez toujours la liste complète). L'import CSV, "
            "<strong>réservé au superadmin</strong>, permet de créer, mettre à jour ou supprimer des comptes en masse à "
            "partir d'un fichier, avec options de confirmation pour les mises à jour et les suppressions.</p>"

            "<h2>Groupes et permissions</h2>"
            "<p>Cette section est <strong>entièrement réservée au superadmin</strong> — un administrateur de domaine n'y a "
            "aucun accès, même pour les utilisateurs ou permissions de son propre domaine.</p>"
            "<h3>Groupes</h3>"
            "<p>Les groupes systèmes (\"Comptes administrateurs\", \"Administrateurs de domaines\", \"Tous les comptes\", "
            "\"Visiteurs\") et les groupes personnalisés que vous créez sont listés en haut de page. Chaque groupe personnalisé "
            "peut être supprimé (sauf les groupes systèmes et le groupe <code>wappos_domain_admins</code>, protégé de la "
            "suppression pour ne pas casser le mécanisme d'administration scopée). Pour chaque groupe, vous pouvez gérer ses "
            "membres et, plus bas sur la page, les permissions d'application qui lui sont accordées.</p>"
            "<h3 id=\"admin-domaine\">Créer un administrateur de domaine</h3>"
            "<ol>"
            "<li>Créez un compte utilisateur normal depuis la page Utilisateurs (ou utilisez un compte existant).</li>"
            "<li>Sur la page Groupes, ouvrez la carte \"Administrateurs de domaines\" et ajoutez ce compte comme membre du "
            "groupe <code>wappos_domain_admins</code>.</li>"
            "<li>Toujours dans cette même carte, cochez le ou les domaines que ce compte doit administrer, puis "
            "enregistrez. C'est cette attribution — pas la seule appartenance au groupe — qui détermine concrètement quels "
            "domaines, utilisateurs et applications ce compte pourra voir et gérer.</li>"
            "</ol>"
            "<p>Un compte membre de <code>wappos_domain_admins</code> mais sans domaine attribué peut se connecter à cette "
            "interface, mais n'y verra aucune donnée exploitable tant qu'aucun domaine ne lui est attribué.</p>"
            "<h3>Permissions d'application</h3>"
            "<p>Chaque application installée expose une ou plusieurs permissions (généralement \"main\", parfois "
            "\"admin\" ou d'autres selon l'application). Depuis la page Groupes ou depuis la page de détail d'une "
            "application, vous choisissez quels groupes ou comptes individuels peuvent y accéder, et réglez ses propriétés "
            "d'affichage (libellé, visibilité de la tuile sur le portail, logo personnalisé).</p>"

            "<h2>Domaines</h2>"
            "<p>Liste tous les domaines et sous-domaines configurés, avec l'état de leur certificat HTTPS. Cliquer sur un "
            "domaine ouvre sa page de détail : configuration, actions disponibles, gestion du certificat (installation, "
            "renouvellement), panneaux de configuration spécifiques, et suppression du domaine (avec option de retirer "
            "aussi ses applications).</p>"
            "<h3>Ajouter un domaine</h3>"
            "<p>Le domaine doit déjà pointer vers ce serveur au niveau DNS. Un certificat Let's Encrypt peut être installé "
            "automatiquement à la création. Pour les domaines DynDNS Wappos/YunoHost (<code>*.nohost.me</code>, "
            "<code>*.noho.st</code>, <code>*.ynh.fr</code>), un mot de passe de récupération optionnel peut être défini.</p>"
            "<h3>Envoi des enregistrements DNS</h3>"
            "<p>Quand le registrar du domaine le permet, un bouton propose de pousser automatiquement les enregistrements "
            "DNS nécessaires (avec un mode simulation avant application réelle).</p>"

            "<h2 id=\"reseau-local\">Accès réseau local</h2>"
            "<p>Cette section, présente sur la page Domaines, permet de rendre Wappos accessible depuis le réseau local "
            "par un nom simple (par exemple <code>wappos.lan</code>) plutôt que par l'adresse IP du serveur — pratique pour "
            "les usages internes qui ne nécessitent pas d'exposition sur Internet. Elle est entièrement réservée au "
            "superadmin.</p>"
            "<h3>Sans rien installer : domaines en .local</h3>"
            "<p>Sans aucune installation supplémentaire, vous pouvez ajouter un domaine se terminant par "
            "<code>.local</code> via le formulaire général \"Ajouter un domaine\", en haut de la page. La résolution "
            "repose alors sur la découverte automatique du réseau (mDNS/Bonjour), un mécanisme standard déjà intégré à la "
            "plupart des ordinateurs (Windows, macOS, Linux). Limite connue et non contournable par ce mécanisme : "
            "<strong>Android ne prend pas en charge le mDNS de façon fiable</strong>, ce qui rend ces domaines "
            "généralement inaccessibles depuis un téléphone ou une tablette Android sur le réseau local.</p>"
            "<h3>Solution fiable sur tous les appareils : AdGuard Home</h3>"
            "<p>Pour un accès local fiable y compris depuis Android, installez AdGuard Home (application disponible dans "
            "le catalogue d'applications). Une fois installé, la carte \"Accès réseau local\" de la page Domaines vous "
            "permet d'activer l'accès local en un clic (domaine <code>wappos.lan</code> créé automatiquement), puis "
            "d'ajouter d'autres domaines en <code>.lan</code> selon vos besoins. Chaque domaine <code>.lan</code> ajouté "
            "crée une réécriture DNS dans AdGuard Home, qui répond alors directement avec l'adresse IP locale du serveur à "
            "tout appareil du réseau qui l'utilise comme serveur DNS (le mDNS n'entre plus en jeu, ce qui explique la "
            "fiabilité sur Android). Le retrait d'un domaine local retire aussi automatiquement la réécriture DNS "
            "associée.</p>"

            "<h2>Applications</h2>"
            "<h3>Applications YunoHost</h3>"
            "<p>Liste les applications installées nativement via YunoHost (hors applications Docker Gate et applications "
            "internes Wappos, qui ne sont pas affichées ici). Pour chaque application : mise à jour, changement de domaine/"
            "chemin, renommage de son libellé, gestion de ses permissions et de ses groupes autorisés, panneaux de "
            "configuration et actions spécifiques à l'application, réglages techniques bruts (réservés aux cas avancés), "
            "et suppression (avec option de purge des données). Un administrateur de domaine peut effectuer toutes ces "
            "actions sur une application déjà installée sur l'un de ses domaines, y compris la supprimer — seules "
            "l'installation d'une nouvelle application (\"Parcourir le catalogue\") et la bascule technique cross-domaine "
            "restent réservées au superadmin.</p>"
            "<h3>Docker Gate</h3>"
            "<p>Docker Gate est l'outil maison qui permet d'installer des applications supplémentaires packagées avec "
            "Docker, même quand elles n'existent pas en paquet YunoHost natif. Depuis cette section : ajout d'une nouvelle "
            "application Docker (assistant guidé : sous-domaine, chemin, visibilité, ressources), démarrage/arrêt/"
            "redémarrage du conteneur, consultation des journaux et des statistiques de ressources en direct, mise à jour "
            "de l'image, modification de la configuration (image, port, chemin de données, variables d'environnement, "
            "limites CPU/mémoire, intégration LDAP), changement de domaine, et suppression. Une page d'audit dédiée liste "
            "les conteneurs, volumes et réseaux orphelins, les images obsolètes, et permet si besoin la désinstallation "
            "complète de Docker CE de la machine.</p>"
            "<p>Comme pour les applications YunoHost, un administrateur de domaine ne voit et ne gère que les applications "
            "Docker installées sur son ou ses domaines (liste, actions, modification, suppression) ; il ne peut pas créer "
            "une application Docker sur un domaine qui ne lui appartient pas. La page d'audit (conteneurs/volumes/réseaux "
            "orphelins, désinstallation de Docker CE) porte sur la machine entière, sans notion de domaine : elle est "
            "réservée au superadmin.</p>"

            "<h2>Diagnostic</h2>"
            "<p><strong>Réservé au superadmin.</strong> Affiche les rapports de diagnostic système de YunoHost (DNS, "
            "certificats, mail, sécurité, services, etc.), permet de relancer un diagnostic complet ou catégorie par "
            "catégorie, et d'ignorer/réactiver certains signalements non pertinents pour votre configuration.</p>"

            "<h2>Sauvegardes</h2>"
            "<p><strong>Réservé au superadmin</strong> — un administrateur de domaine n'a aucun accès aux sauvegardes, "
            "même pour ses propres domaines. Cette page permet de créer une archive (globale ou limitée à certaines "
            "applications), de consulter l'historique des archives existantes avec leur contenu détaillé, de télécharger, "
            "restaurer ou supprimer une archive, de configurer une planification automatique (fréquence, périmètre, durée "
            "de rétention), et de prévisualiser quelles archives seraient purgées par la politique de rétention en "
            "vigueur.</p>"

            "<h2>Sécurité</h2>"
            "<p><strong>Réservé au superadmin.</strong> Permet d'activer ou de désactiver l'authentification SSH par mot "
            "de passe (la connexion par clé reste toujours possible), et affiche une synthèse de sécurité (ancienneté du "
            "mot de passe root, etc.).</p>"

            "<h2>Système</h2>"
            "<p>L'ensemble de ce menu est <strong>réservé au superadmin</strong>.</p>"
            "<ul>"
            "<li><strong>Mises à jour</strong> : liste les applications et catégories système à mettre à jour, avec "
            "lancement de la mise à jour depuis la page.</li>"
            "<li><strong>Migrations</strong> : liste les migrations YunoHost en attente ou déjà effectuées, avec "
            "possibilité de les lancer (une par une ou toutes) après acceptation de l'avertissement correspondant.</li>"
            "<li><strong>Régénération de la configuration</strong> : force YunoHost à réappliquer sa configuration système "
            "(mode simulation ou application réelle).</li>"
            "<li><strong>Mot de passe root</strong>, <strong>redémarrage</strong> et <strong>arrêt</strong> du serveur : "
            "ces trois actions exigent la saisie d'un mot de confirmation avant validation, étant donné leur impact "
            "immédiat sur l'ensemble du serveur et de tous ses utilisateurs.</li>"
            "<li><strong>Services</strong> : liste des services systemd et des services Wappos, avec détail, journaux, et "
            "actions de démarrage/arrêt/redémarrage/activation/désactivation par service.</li>"
            "<li><strong>Journaux</strong> : historique des opérations effectuées par YunoHost, consultables par jour, "
            "avec possibilité de partager un journal individuel via le service de collage sécurisé de YunoHost.</li>"
            "<li><strong>Pare-feu</strong> : état des ports TCP/UDP ouverts, activation/désactivation de l'UPnP, ouverture "
            "ou fermeture de ports.</li>"
            "<li><strong>Stockage</strong> : liste des disques et points de montage avec leur occupation, et rapports "
            "SMART pour la santé des disques.</li>"
            "<li><strong>Performance</strong> : tableau de bord de supervision (Prometheus) des composants Wappos "
            "(portail, interface d'administration, API) — nécessite qu'un accès Prometheus dédié ait été configuré sur le "
            "serveur, sans quoi la page l'indique simplement comme indisponible.</li>"
            "<li><strong>Réglages avancés</strong> : panneaux de configuration globaux de YunoHost, dont les réglages de "
            "compression des sauvegardes.</li>"
            "</ul>"

            "<h2>Pied de page</h2>"
            "<p>Présent en bas de chaque page une fois connecté : lien vers cette documentation, numéro de version de "
            "l'interface, et lien vers BYRTN.</p>"
        ),
        "en": (
            "<h2>About this interface</h2>"
            "<p>Wappos Admin is your Wappos server's technical administration interface, reserved for administrator "
            "accounts. It relies on YunoHost, the server operating system that actually manages accounts, domains, "
            "certificates, applications and backups — this interface only displays and drives what YunoHost already does, "
            "never duplicating its security logic. You are logged in here as a <strong>superadmin</strong>: you have full "
            "access to every function described below, with no domain restriction.</p>"
            "<p>For end-user documentation (the app portal, profile, password), see the Documentation page of the portal "
            "(the \"Administration\" link in its footer goes the other way).</p>"

            "<h2>Two administrator profiles</h2>"
            "<p>Wappos distinguishes two levels of administrator account:</p>"
            "<ul>"
            "<li><strong>Superadmin</strong>: a member of the system <code>admins</code> group. Full, unrestricted access "
            "to every function of this interface — that's you.</li>"
            "<li><strong>Domain administrator</strong>: a member of the <code>wappos_domain_admins</code> group, never of "
            "the <code>admins</code> group. A domain administrator only sees and manages what belongs to their domain(s): "
            "their users, applications, permissions, and domain configuration. They have no access to any function "
            "affecting the server as a whole (see the exclusion list further down).</li>"
            "</ul>"
            "<p>A domain administrator has no separate technical account: it is an ordinary user account, simply added to "
            "the <code>wappos_domain_admins</code> group and then associated with one or more domains. See \"Creating a "
            "domain administrator\" below for the full procedure.</p>"

            "<h2>Dashboard (Home)</h2>"
            "<p>The home page shows a shortcut menu to the main sections (Users, Domains, Applications, and for you only: "
            "Groups and permissions, Diagnosis, Backups, System), plus a summary dashboard reserved for the superadmin: "
            "disk space per volume, system service status, latest diagnosis result, failed system units, last backup "
            "date, and number of available updates (apps and system). Every dashboard tile is clickable and leads "
            "straight to the corresponding page for more detail.</p>"

            "<h2>Users</h2>"
            "<p>Lists every account on the server. For you, each administrator account shows a badge (\"Superadmin\" or "
            "\"Domain admin: &lt;domain(s)&gt;\"), and the list is sorted to bring administrator accounts to the top.</p>"
            "<h3>Creating an account</h3>"
            "<p>From the bottom of the Users page: username, mail domain, full name and initial password. The username "
            "may only contain lowercase letters, digits, dots and underscores.</p>"
            "<h3>Editing an account</h3>"
            "<p>Click an account in the list to land directly on its edit page: full name, primary email address, "
            "aliases and forwarding addresses, mailbox quota, public SSH keys (add/remove), password reset, and account "
            "deletion (with an option to purge its data).</p>"
            "<h3>CSV export / import</h3>"
            "<p>CSV export downloads the account list (filtered to your domains if you were a domain admin — not "
            "relevant to you as superadmin, who always get the full list). CSV import, <strong>reserved to the "
            "superadmin</strong>, lets you bulk-create, update or delete accounts from a file, with confirmation options "
            "for updates and deletions.</p>"

            "<h2>Groups and permissions</h2>"
            "<p>This section is <strong>entirely reserved to the superadmin</strong> — a domain administrator has no "
            "access to it at all, even for their own domain's users or permissions.</p>"
            "<h3>Groups</h3>"
            "<p>System groups (\"Administrator accounts\", \"Domain administrators\", \"All accounts\", \"Visitors\") and "
            "any custom groups you create are listed at the top of the page. Any custom group can be deleted (except "
            "system groups and the <code>wappos_domain_admins</code> group, protected from deletion so as not to break "
            "the scoped-administration mechanism). For each group, you can manage its members and, further down the page, "
            "the app permissions granted to it.</p>"
            "<h3 id=\"admin-domaine\">Creating a domain administrator</h3>"
            "<ol>"
            "<li>Create a normal user account from the Users page (or use an existing one).</li>"
            "<li>On the Groups page, open the \"Domain administrators\" card and add that account as a member of the "
            "<code>wappos_domain_admins</code> group.</li>"
            "<li>Still in that same card, check the domain(s) this account should administer, then save. It is this "
            "assignment — not mere group membership — that actually determines which domains, users and applications this "
            "account will be able to see and manage.</li>"
            "</ol>"
            "<p>An account that belongs to <code>wappos_domain_admins</code> but has no domain assigned can log in to "
            "this interface, but won't see any usable data until a domain is assigned to it.</p>"
            "<h3>Application permissions</h3>"
            "<p>Every installed application exposes one or more permissions (usually \"main\", sometimes \"admin\" or "
            "others depending on the app). From the Groups page or from an application's detail page, you choose which "
            "groups or individual accounts may access it, and set its display properties (label, tile visibility on the "
            "portal, custom logo).</p>"

            "<h2>Domains</h2>"
            "<p>Lists every configured domain and subdomain, with its HTTPS certificate status. Clicking a domain opens "
            "its detail page: configuration, available actions, certificate management (install, renew), app-specific "
            "config panels, and domain deletion (with an option to also remove its applications).</p>"
            "<h3>Adding a domain</h3>"
            "<p>The domain must already point to this server at the DNS level. A Let's Encrypt certificate can be "
            "installed automatically on creation. For Wappos/YunoHost DynDNS domains (<code>*.nohost.me</code>, "
            "<code>*.noho.st</code>, <code>*.ynh.fr</code>), an optional recovery password can be set.</p>"
            "<h3>Pushing DNS records</h3>"
            "<p>When the domain's registrar supports it, a button lets you automatically push the required DNS records "
            "(with a dry-run mode before actually applying).</p>"

            "<h2 id=\"reseau-local\">Local network access</h2>"
            "<p>This section, on the Domains page, makes Wappos reachable from the local network by a simple name (e.g. "
            "<code>wappos.lan</code>) instead of the server's IP address — handy for internal uses that don't need "
            "Internet exposure. It is entirely reserved to the superadmin.</p>"
            "<h3>Without installing anything: .local domains</h3>"
            "<p>Without any extra installation, you can add a domain ending in <code>.local</code> via the general \"Add "
            "a domain\" form at the top of the page. Resolution then relies on automatic network discovery (mDNS/"
            "Bonjour), a standard mechanism already built into most computers (Windows, macOS, Linux). Known, "
            "non-bypassable limitation of this mechanism: <strong>Android does not support mDNS reliably</strong>, which "
            "generally makes these domains unreachable from an Android phone or tablet on the local network.</p>"
            "<h3>Reliable on every device: AdGuard Home</h3>"
            "<p>For reliable local access including from Android, install AdGuard Home (available in the app catalog). "
            "Once installed, the \"Local network access\" card on the Domains page lets you enable local access in one "
            "click (a <code>wappos.lan</code> domain is created automatically), then add more <code>.lan</code> domains "
            "as needed. Each added <code>.lan</code> domain creates a DNS rewrite in AdGuard Home, which then answers "
            "directly with the server's local IP address to any device on the network using it as a DNS server (mDNS is "
            "no longer involved, which is why it's reliable on Android). Removing a local domain also automatically "
            "removes its associated DNS rewrite.</p>"

            "<h2>Applications</h2>"
            "<h3>YunoHost applications</h3>"
            "<p>Lists applications installed natively through YunoHost (excluding Docker Gate apps and Wappos's own "
            "internal apps, which aren't shown here). For each application: upgrade, change domain/path, rename its "
            "label, manage its permissions and authorized groups, app-specific config panels and actions, raw technical "
            "settings (reserved for advanced cases), and removal (with an option to purge its data). A domain "
            "administrator can perform all of these actions on an application already installed on one of their domains, "
            "including removing it — only installing a new application (\"Browse the catalog\") and the cross-domain "
            "technical toggle remain reserved to the superadmin.</p>"
            "<h3>Docker Gate</h3>"
            "<p>Docker Gate is the in-house tool that lets you install extra applications packaged with Docker, even when "
            "no native YunoHost package exists for them. From this section: adding a new Docker app (guided wizard: "
            "subdomain, path, visibility, resources), starting/stopping/restarting the container, viewing live logs and "
            "resource stats, updating the image, editing configuration (image, port, data path, environment variables, "
            "CPU/memory limits, LDAP integration), changing domain, and removal. A dedicated audit page lists orphan "
            "containers, volumes and networks, stale images, and, if needed, lets you fully uninstall Docker CE from the "
            "machine.</p>"
            "<p>As with YunoHost applications, a domain administrator only sees and manages Docker applications installed "
            "on their own domain(s) (list, actions, editing, removal); they cannot create a Docker application on a "
            "domain they don't own. The audit page (orphan containers/volumes/networks, uninstalling Docker CE) covers "
            "the whole machine, with no notion of domain: it is reserved to the superadmin.</p>"

            "<h2>Diagnosis</h2>"
            "<p><strong>Reserved to the superadmin.</strong> Shows YunoHost's system diagnosis reports (DNS, "
            "certificates, mail, security, services, etc.), lets you re-run a full or per-category diagnosis, and lets "
            "you ignore/unignore reports that aren't relevant to your setup.</p>"

            "<h2>Backups</h2>"
            "<p><strong>Reserved to the superadmin</strong> — a domain administrator has no access to backups at all, "
            "even for their own domains. This page lets you create an archive (full or limited to specific apps), browse "
            "the history of existing archives with their detailed content, download, restore or delete an archive, "
            "configure an automatic schedule (frequency, scope, retention period), and preview which archives the "
            "current retention policy would prune.</p>"

            "<h2>Security</h2>"
            "<p><strong>Reserved to the superadmin.</strong> Lets you enable or disable SSH password authentication (key-"
            "based login always remains possible), and shows a security summary (root password age, etc.).</p>"

            "<h2>System</h2>"
            "<p>This whole menu is <strong>reserved to the superadmin</strong>.</p>"
            "<ul>"
            "<li><strong>Updates</strong>: lists applications and system categories to update, with the update itself "
            "launchable from the page.</li>"
            "<li><strong>Migrations</strong>: lists pending or already-run YunoHost migrations, with the ability to run "
            "them (one at a time or all) after accepting the corresponding warning.</li>"
            "<li><strong>Regenerate configuration</strong>: forces YunoHost to reapply its system configuration (dry-run "
            "or real application).</li>"
            "<li><strong>Root password</strong>, <strong>reboot</strong> and <strong>shutdown</strong> of the server: "
            "these three actions require typing a confirmation word before proceeding, given their immediate impact on "
            "the whole server and every one of its users.</li>"
            "<li><strong>Services</strong>: list of systemd services and Wappos services, with detail, logs, and per-"
            "service start/stop/restart/enable/disable actions.</li>"
            "<li><strong>Logs</strong>: history of operations performed by YunoHost, browsable by day, with the ability "
            "to share an individual log via YunoHost's secure paste service.</li>"
            "<li><strong>Firewall</strong>: status of open TCP/UDP ports, enabling/disabling UPnP, opening or closing "
            "ports.</li>"
            "<li><strong>Storage</strong>: list of disks and mount points with their usage, and SMART reports for disk "
            "health.</li>"
            "<li><strong>Performance</strong>: a monitoring dashboard (Prometheus) for Wappos's own components (portal, "
            "admin interface, API) — requires a dedicated Prometheus credential to have been configured on the server, "
            "otherwise the page simply reports it as unavailable.</li>"
            "<li><strong>Advanced settings</strong>: YunoHost's global configuration panels, including backup "
            "compression settings.</li>"
            "</ul>"

            "<h2>Footer</h2>"
            "<p>Present at the bottom of every page once logged in: a link to this documentation, the interface's "
            "version number, and a link to BYRTN.</p>"
        ),
    },

    "page_body_documentation_domain_admin": {
        "fr": (
            "<h2>Votre rôle : administrateur de domaine</h2>"
            "<p>Vous êtes connecté à Wappos Admin en tant qu'<strong>administrateur de domaine</strong> : vous gérez "
            "uniquement ce qui appartient au(x) domaine(s) qui vous ont été attribués par le superadmin de ce serveur — "
            "utilisateurs, applications, permissions et configuration de ce domaine. Vous n'êtes membre d'aucun groupe "
            "d'administration système global, et vous n'avez accès à aucune fonction affectant le serveur dans son "
            "ensemble.</p>"

            "<h2>Ce que vous pouvez gérer</h2>"
            "<h3>Utilisateurs</h3>"
            "<p>La liste et les actions (création, modification, réinitialisation de mot de passe, clés SSH, "
            "suppression, export CSV) ne portent que sur les comptes dont l'adresse mail appartient à votre ou vos "
            "domaines.</p>"
            "<h3>Domaines</h3>"
            "<p>Vous voyez et gérez uniquement le ou les domaines qui vous ont été attribués (configuration, certificat, "
            "envoi DNS, suppression). Vous pouvez aussi créer un nouveau domaine à condition que ce soit un "
            "<strong>sous-domaine strict</strong> d'un domaine qui vous appartient déjà (par exemple "
            "<code>boutique.mondomaine.fr</code> si <code>mondomaine.fr</code> vous appartient) — au-delà, la création "
            "d'un domaine indépendant reste réservée au superadmin.</p>"
            "<h3>Applications</h3>"
            "<p>Vous gérez les applications déjà installées sur vos domaines : mise à jour, changement de domaine/chemin "
            "(vers un domaine qui vous appartient également), renommage, permissions et groupes autorisés, panneaux de "
            "configuration et actions spécifiques, réglages techniques bruts, et <strong>suppression</strong>. Seule "
            "l'installation d'une nouvelle application depuis le catalogue reste réservée au superadmin.</p>"
            "<h3>Permissions</h3>"
            "<p>Pour les permissions des applications installées sur vos domaines : choix des groupes/comptes autorisés, "
            "et réglages d'affichage (libellé, visibilité de la tuile, logo).</p>"
            "<h3>Docker Gate</h3>"
            "<p>Comme pour les applications YunoHost, vous ne voyez et ne gérez que les applications Docker installées "
            "sur votre ou vos domaines, et ne pouvez pas en créer une nouvelle sur un domaine qui ne vous appartient pas. "
            "La page d'audit Docker (nettoyage des conteneurs/volumes/réseaux orphelins, désinstallation de Docker CE) "
            "porte sur la machine entière et vous est inaccessible.</p>"

            "<h2>Ce que vous ne pouvez pas faire</h2>"
            "<p>Les sections suivantes sont entièrement réservées au superadmin et n'apparaissent pas, ou renverront une "
            "erreur d'accès si vous tentiez d'y accéder directement par leur adresse : Groupes et permissions (y compris "
            "la gestion des groupes et l'attribution des domaines), Diagnostic, Sauvegardes, Sécurité, et tout le menu "
            "Système (mises à jour, migrations, régénération de configuration, mot de passe root, redémarrage, arrêt, "
            "services, journaux, pare-feu, stockage, performance, réglages avancés). L'installation d'une nouvelle "
            "application, la bascule technique cross-domaine, l'ajout d'un domaine local (<code>.lan</code>) et l'import "
            "CSV d'utilisateurs sont également réservés au superadmin.</p>"
            "<p>Pour toute action bloquée qui vous semble nécessaire, contactez le superadmin de ce serveur.</p>"
        ),
        "en": (
            "<h2>Your role: domain administrator</h2>"
            "<p>You are logged in to Wappos Admin as a <strong>domain administrator</strong>: you only manage what "
            "belongs to the domain(s) assigned to you by this server's superadmin — users, applications, permissions and "
            "configuration for that domain. You are not a member of any global system administration group, and you have "
            "no access to any function affecting the server as a whole.</p>"

            "<h2>What you can manage</h2>"
            "<h3>Users</h3>"
            "<p>The list and its actions (creation, editing, password reset, SSH keys, deletion, CSV export) only cover "
            "accounts whose email address belongs to your domain(s).</p>"
            "<h3>Domains</h3>"
            "<p>You see and manage only the domain(s) assigned to you (configuration, certificate, DNS push, deletion). "
            "You can also create a new domain provided it is a <strong>strict subdomain</strong> of a domain you already "
            "own (e.g. <code>shop.mydomain.com</code> if you own <code>mydomain.com</code>) — beyond that, creating an "
            "independent domain remains reserved to the superadmin.</p>"
            "<h3>Applications</h3>"
            "<p>You manage applications already installed on your domains: upgrade, changing domain/path (to a domain "
            "you also own), renaming, permissions and authorized groups, app-specific config panels and actions, raw "
            "technical settings, and <strong>removal</strong>. Only installing a new application from the catalog "
            "remains reserved to the superadmin.</p>"
            "<h3>Permissions</h3>"
            "<p>For permissions of applications installed on your domains: choosing authorized groups/accounts, and "
            "display settings (label, tile visibility, logo).</p>"
            "<h3>Docker Gate</h3>"
            "<p>As with YunoHost applications, you only see and manage Docker applications installed on your own "
            "domain(s), and cannot create a new one on a domain you don't own. The Docker audit page (cleaning up orphan "
            "containers/volumes/networks, uninstalling Docker CE) covers the whole machine and is not accessible to "
            "you.</p>"

            "<h2>What you cannot do</h2>"
            "<p>The following sections are entirely reserved to the superadmin and either won't appear, or will return "
            "an access error if you tried to reach them directly by address: Groups and permissions (including group "
            "management and domain assignment), Diagnosis, Backups, Security, and the entire System menu (updates, "
            "migrations, configuration regeneration, root password, reboot, shutdown, services, logs, firewall, storage, "
            "performance, advanced settings). Installing a new application, the cross-domain technical toggle, adding a "
            "local (<code>.lan</code>) domain, and CSV user import are also reserved to the superadmin.</p>"
            "<p>For anything blocked that you believe you need, contact this server's superadmin.</p>"
        ),
    },
}


def t(key, lang, **kwargs):
    entry = STRINGS.get(key)
    if entry is None:
        return key
    template = entry.get(lang) or entry.get(DEFAULT_LANG) or key
    return template.format(**kwargs) if kwargs else template


def normalize_lang(lang):
    if lang and lang.lower() in LANGS:
        return lang.lower()
    return DEFAULT_LANG
