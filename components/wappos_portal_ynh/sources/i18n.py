# Auteur : Patrick Ritaine

DEFAULT_LANG = "fr"
LANGS = ("fr", "en")

STRINGS = {
    "edit_profile": {"fr": "Éditer mon profil", "en": "Edit my profile"},
    "logout": {"fr": "Déconnexion", "en": "Log out"},
    "nav_documentation": {"fr": "Documentation", "en": "Documentation"},
    "nav_support": {"fr": "Support", "en": "Support"},
    "nav_administration": {"fr": "Administration", "en": "Administration"},

    "web_search_fallback": {"fr": "le web", "en": "the web"},
    "web_search_placeholder": {"fr": "Rechercher sur {engine}", "en": "Search {engine}"},
    "aria_search": {"fr": "Rechercher", "en": "Search"},
    "app_search_placeholder": {"fr": "Rechercher une application…", "en": "Search for an app…"},
    "aria_search_app": {"fr": "Rechercher une application", "en": "Search for an app"},
    "no_app_available": {"fr": "Aucune application accessible.", "en": "No app available."},

    "pwa_install_link": {"fr": "Installer l'application", "en": "Install the app"},
    "pwa_install_ios_prompt": {"fr": "Installer Wappos : appuyez sur Partager puis « Sur l'écran d'accueil ».", "en": "Install Wappos: tap Share, then \"Add to Home Screen\"."},
    "pwa_install_unsupported": {"fr": "Ce navigateur ne propose pas l'installation automatique. Ouvrez son menu et cherchez « Ajouter à l'écran d'accueil », ou essayez avec Chrome/Edge.", "en": "This browser doesn't offer automatic installation. Open its menu and look for \"Add to Home Screen\", or try Chrome/Edge."},
    "pwa_install_dismiss": {"fr": "Fermer", "en": "Close"},

    "title_login": {"fr": "Connexion — WAPPOS PORTAL", "en": "Log in — WAPPOS PORTAL"},
    "username_label": {"fr": "Nom du compte", "en": "Account name"},
    "username_placeholder": {"fr": "Nom du compte", "en": "Account name"},
    "password_label": {"fr": "Mot de passe", "en": "Password"},
    "password_placeholder": {"fr": "Mot de passe", "en": "Password"},
    "toggle_password_show": {"fr": "Afficher", "en": "Show"},
    "toggle_password_hide": {"fr": "Masquer", "en": "Hide"},
    "btn_login": {"fr": "Connexion", "en": "Log in"},
    "err_possibly_invalid_username": {
        "fr": "Identifiant peut-être incorrect.",
        "en": "Username may be incorrect.",
    },
    "err_possibly_invalid_password": {
        "fr": "Mot de passe peut-être incorrect.",
        "en": "Password may be incorrect.",
    },
    "err_server_unreachable": {
        "fr": "Impossible de contacter le serveur, réessaie.",
        "en": "Unable to reach the server, try again.",
    },
    "err_session_expired": {
        "fr": "Ta session a expiré, reconnecte-toi.",
        "en": "Your session has expired, please log in again.",
    },
    "err_access_denied": {
        "fr": "Tu n'as pas la permission d'accéder à cette application.",
        "en": "You don't have permission to access that application.",
    },
    "msg_protected": {
        "fr": "Connecte-toi pour accéder à cette page.",
        "en": "Log in to access this page.",
    },

    "title_profile": {"fr": "Éditer mon profil — WAPPOS PORTAL", "en": "Edit my profile — WAPPOS PORTAL"},
    "h1_edit_profile": {"fr": "Éditer mon profil", "en": "Edit my profile"},
    "back_to_portal": {"fr": "Retour au portail", "en": "Back to portal"},
    "readonly_field_note": {
        "fr": "Pour modifier ce paramètre, contactez votre administrateur.",
        "en": "To change this setting, contact your administrator.",
    },
    "h2_personal_info": {"fr": "Informations personnelles", "en": "Personal information"},
    "fullname_label": {"fr": "Nom complet", "en": "Full name"},
    "mail_label": {"fr": "Adresse mail principale", "en": "Primary email address"},
    "username_field_label": {"fr": "Nom d'utilisateur", "en": "Username"},
    "btn_save": {"fr": "Enregistrer", "en": "Save"},
    "h3_aliases": {"fr": "Adresses de courriel (alias)", "en": "Email addresses (aliases)"},
    "alias_placeholder": {"fr": "nouvel-alias@wappos.fr", "en": "new-alias@wappos.fr"},
    "h3_forwards": {"fr": "Adresses de transfert d'emails", "en": "Email forwarding addresses"},
    "forward_placeholder": {"fr": "adresse@exemple.fr", "en": "address@example.com"},
    "btn_add": {"fr": "Ajouter", "en": "Add"},
    "btn_remove": {"fr": "Retirer", "en": "Remove"},
    "h2_change_password": {"fr": "Changer de mot de passe", "en": "Change password"},
    "current_password_label": {"fr": "Mot de passe actuel", "en": "Current password"},
    "new_password_label": {"fr": "Nouveau mot de passe", "en": "New password"},
    "confirm_password_label": {"fr": "Confirmer le nouveau mot de passe", "en": "Confirm new password"},

    "h2_browser_settings": {
        "fr": "Paramètres du navigateur",
        "en": "Browser settings",
    },
    "language_label": {"fr": "Langue", "en": "Language"},
    "language_option_fr": {"fr": "Français", "en": "French"},
    "language_option_en": {"fr": "English", "en": "English"},
    "theme_label": {"fr": "Thème", "en": "Theme"},
    "theme_option_system": {"fr": "Système", "en": "System"},
    "theme_option_light": {"fr": "Clair", "en": "Light"},
    "theme_option_dark": {"fr": "Sombre", "en": "Dark"},
    "theme_option_black": {"fr": "Noir", "en": "Black"},
    "theme_option_legacy": {"fr": "Historique", "en": "Legacy"},
    "theme_option_halloween": {"fr": "Halloween", "en": "Halloween"},
    "theme_option_cupcake": {"fr": "Cupcake", "en": "Cupcake"},
    "theme_option_nord": {"fr": "Nord", "en": "Nord"},
    "browser_settings_auto_apply": {
        "fr": "Les changements s'appliquent immédiatement.",
        "en": "Changes apply immediately.",
    },
    "logout_everywhere_note": {
        "fr": "Ceci vous déconnectera de tous vos autres appareils.",
        "en": "This will log you out of all your other devices.",
    },

    "page_title_documentation": {"fr": "Documentation", "en": "Documentation"},
    "page_title_support": {"fr": "Support", "en": "Support"},
    "page_body_coming_soon": {"fr": "Contenu à venir.", "en": "Content coming soon."},
    "page_body_documentation": {
        "fr": (
            "<h2>Qu'est-ce que Wappos ?</h2>"
            "<p>Wappos est un produit serveur clé en main conçu par <strong>BYRTN</strong>, intégrateur en souveraineté numérique. "
            "Son objectif : permettre à une entreprise de reprendre le contrôle de ses données et de ses outils numériques du quotidien "
            "(fichiers, messagerie, agenda, bureautique, gestion, applications métier...) en les hébergeant elle-même, sur son propre "
            "serveur, plutôt que de dépendre d'abonnements mensuels chez des géants du cloud (Microsoft, Google...). "
            "Moins d'abonnements, plus d'autonomie, une infrastructure qui appartient réellement à l'entreprise qui l'utilise.</p>"

            "<h2>Comment Wappos est construit</h2>"
            "<p>Wappos s'appuie sur YunoHost, un système d'exploitation serveur open source qui sert de base à "
            "l'ensemble du système Wappos. C'est cette base qui gère "
            "les comptes utilisateurs, la connexion unique, les certificats de sécurité (HTTPS), les sauvegardes, et un catalogue "
            "d'applications déjà prêtes à installer. Par-dessus cette base, BYRTN a développé <strong>Docker Gate</strong>, un outil "
            "maison qui permet d'ajouter facilement des applications supplémentaires packagées avec Docker, même quand elles "
            "n'existent pas nativement pour le système — sans jamais dupliquer la gestion des comptes ou de la sécurité, qui reste "
            "toujours entièrement pilotée par le système. Enfin, ce portail que vous utilisez actuellement, <strong>Wappos Portal</strong>, "
            "est une interface maison développée par BYRTN par-dessus le système : une vitrine simplifiée et personnalisée sur vos "
            "applications et vos réglages de compte, pensée pour être plus simple à utiliser au quotidien que l'interface technique "
            "standard d'un serveur auto-hébergé — tout en s'appuyant, en coulisses, sur les mêmes mécanismes de sécurité et "
            "d'authentification que le système lui-même. Concrètement, quand vous vous connectez, changez votre mot de passe ou "
            "ajoutez un alias de courriel, c'est toujours le système qui vérifie et applique la demande — ce portail ne fait jamais "
            "de gestion de compte \"maison\" en parallèle.</p>"

            "<h2>Connexion unique (SSO)</h2>"
            "<p>Le système centralise tous les comptes utilisateurs dans un unique annuaire LDAP — une base de données spécialisée "
            "dans le stockage sécurisé des comptes et des mots de passe, standard largement utilisé dans les infrastructures "
            "professionnelles. En pratique, pour vous, cela se traduit par une <strong>connexion unique</strong> (souvent appelée "
            "SSO, pour \"Single Sign-On\") : un seul identifiant et un seul mot de passe suffisent pour accéder à toutes les "
            "applications installées sur le système, sans avoir à vous reconnecter séparément à chacune, et sans avoir à retenir "
            "un mot de passe différent par outil. Tant que votre session reste active dans votre navigateur, vous passez librement "
            "d'une application à l'autre, et du portail à une application puis à une autre, sans qu'on vous redemande jamais vos "
            "identifiants entre-temps.</p>"

            "<h2>À quoi sert ce portail</h2>"
            "<p>Wappos Portal est votre point d'entrée unique et quotidien vers les applications installées sur ce serveur, "
            "et vers les réglages de votre propre compte utilisateur. Vous n'avez pas besoin de connaître le système ni Docker Gate "
            "pour vous en servir : ce qui suit couvre en détail, étape par étape, chaque fonctionnalité que vous pouvez utiliser "
            "directement depuis ce portail.</p>"

            "<h2>Se connecter</h2>"
            "<p>La page de connexion demande votre nom de compte et votre mot de passe. Ce sont les mêmes identifiants que ceux "
            "créés ou communiqués par l'administrateur de votre serveur. Cliquez dans le champ \"Nom du compte\", saisissez votre "
            "identifiant, puis cliquez dans le champ \"Mot de passe\" (ou utilisez la touche Tabulation pour y passer directement) "
            "et saisissez votre mot de passe. Cliquez enfin sur le bouton \"Connexion\" (ou appuyez sur la touche Entrée) pour "
            "valider. Une fois connecté, vous restez authentifié tant que votre session est valide (jusqu'à déconnexion explicite, "
            "ou expiration de session selon la configuration du serveur) — vous n'avez pas besoin de ressaisir vos identifiants à "
            "chaque nouvelle page ou chaque nouvelle application, grâce à la connexion unique décrite plus haut.</p>"

            "<h2>La page d'accueil</h2>"
            "<p>Une fois connecté, la page d'accueil affiche une tuile par application à laquelle vous avez accès (l'accès à chaque "
            "application est décidé par l'administrateur, via les permissions du système — ce portail se contente d'afficher ce que "
            "le système vous autorise à voir).</p>"

            "<h3>Ouvrir une application</h3>"
            "<ol>"
            "<li>Cliquez une seule fois sur la tuile de l'application souhaitée.</li>"
            "<li>Un nouvel onglet de votre navigateur s'ouvre automatiquement avec l'application demandée — votre portail, lui, "
            "reste affiché sans aucun changement dans l'onglet d'origine, toujours ouvert derrière.</li>"
            "<li>Utilisez l'application normalement dans ce nouvel onglet, comme n'importe quel site web.</li>"
            "<li>Une fois votre travail terminé dans l'application, fermez simplement cet onglet (cliquez sur la petite croix "
            "\"×\" de l'onglet, ou utilisez le raccourci clavier Ctrl+W sur Windows/Linux, Cmd+W sur Mac) pour revenir directement "
            "à l'onglet du portail, resté ouvert et toujours connecté entre-temps — vous n'avez besoin de vous reconnecter à rien.</li>"
            "</ol>"
            "<p>Vous pouvez aussi garder plusieurs applications ouvertes en même temps, chacune dans son propre onglet, et naviguer "
            "librement entre elles et le portail : cliquez directement sur l'onglet souhaité en haut de votre navigateur, ou utilisez "
            "le raccourci Ctrl+Tab (Cmd+Option+flèche droite sur Mac) pour passer au prochain onglet, Ctrl+Maj+Tab pour revenir au "
            "précédent. Fermer un onglet d'application ne déconnecte jamais votre session ni celle des autres onglets ouverts.</p>"

            "<h3>Réorganiser les tuiles</h3>"
            "<p>Cliquez sur une tuile et maintenez le clic enfoncé (le curseur change généralement d'aspect), déplacez la souris "
            "jusqu'à l'endroit voulu parmi les autres tuiles, puis relâchez le clic pour déposer la tuile à son nouvel emplacement. "
            "L'ordre choisi est mémorisé pour vous, individuellement : chaque utilisateur du serveur peut avoir son propre ordre, "
            "sans affecter celui des autres.</p>"

            "<h3>Filtrer les applications</h3>"
            "<p>Cliquez dans le champ de recherche situé au-dessus des tuiles, puis tapez un ou plusieurs mots du nom de "
            "l'application recherchée. Les tuiles correspondantes restent affichées, les autres se masquent immédiatement à mesure "
            "de votre saisie, sans recharger la page. Effacez le texte saisi (ou rechargez la page) pour réafficher toutes les tuiles.</p>"

            "<h3>Rechercher sur le web</h3>"
            "<p>Si l'administrateur a configuré un moteur de recherche par défaut pour votre domaine, une seconde barre de recherche "
            "est disponible au-dessus des tuiles. Cliquez dedans, tapez votre recherche, puis validez avec Entrée ou en cliquant sur "
            "le bouton en forme de loupe : les résultats s'ouvrent directement dans un nouvel onglet, comme pour une application, "
            "en laissant votre portail intact dans l'onglet d'origine.</p>"

            "<h2>Éditer votre profil</h2>"
            "<p>Accessible en cliquant sur l'icône crayon à côté de votre nom, en haut de la page, ou via le lien \"Retour au portail\" "
            "puis l'icône crayon. La page est organisée en plusieurs blocs indépendants, chacun avec sa propre action d'enregistrement "
            "(modifier votre nom n'a par exemple aucun impact sur votre mot de passe, et inversement).</p>"

            "<h3>Informations personnelles</h3>"
            "<ul>"
            "<li><strong>Nom complet</strong> : librement modifiable, c'est le nom affiché dans l'en-tête du portail.</li>"
            "<li><strong>Adresse mail principale</strong> : affichée en lecture seule (champ grisé) sur ce serveur — sa modification est "
            "réservée à l'administrateur. Marquée d'un astérisque, avec la note explicative correspondante.</li>"
            "<li><strong>Nom d'utilisateur</strong> : jamais modifiable, quel que soit le serveur — c'est l'identifiant unique de votre "
            "compte, utilisé pour vous authentifier. Marqué du même astérisque.</li>"
            "</ul>"
            "<p>Pour modifier votre nom complet : cliquez dans le champ \"Nom complet\", effacez le texte existant si besoin, saisissez "
            "le nouveau nom, puis cliquez sur le bouton \"Enregistrer\" tout en bas de la carte pour valider le changement.</p>"

            "<h3>Adresses de courriel (alias)</h3>"
            "<p>Un alias est une adresse supplémentaire qui reçoit le courrier au même endroit que votre adresse principale — utile, "
            "par exemple, pour recevoir aussi bien sur <em>prenom.nom@domaine</em> que sur <em>contact@domaine</em>.</p>"
            "<p><strong>Ajouter un alias</strong> : cliquez dans le champ de saisie prévu à cet effet, tapez la nouvelle adresse "
            "complète, puis cliquez sur le bouton \"Ajouter\" juste à côté — l'alias apparaît alors immédiatement dans la liste "
            "au-dessus. <strong>Supprimer un alias</strong> : cliquez sur le lien \"Supprimer\" affiché à côté de l'adresse concernée "
            "dans la liste ; la suppression est immédiate, sans confirmation supplémentaire à ce jour.</p>"

            "<h3>Adresses de transfert d'emails</h3>"
            "<p>Une adresse de transfert renvoie une copie de votre courrier vers une autre boîte mail (externe ou interne) — utile "
            "si vous consultez aussi votre messagerie ailleurs. Ajout et suppression fonctionnent exactement de la même façon que "
            "pour les alias, décrite juste au-dessus.</p>"

            "<h3>Changer de mot de passe</h3>"
            "<ol>"
            "<li>Cliquez dans le champ \"Nouveau mot de passe\" et saisissez votre nouveau mot de passe.</li>"
            "<li>Si vous voulez vérifier ce que vous venez de taper, cliquez sur le lien \"Afficher\" à droite du champ : la saisie "
            "apparaît alors en clair (le lien devient \"Masquer\", cliquez de nouveau dessus pour re-cacher la saisie).</li>"
            "<li>Cliquez dans le champ \"Confirmer le nouveau mot de passe\" et retapez exactement le même mot de passe.</li>"
            "<li>Cliquez sur le bouton \"Enregistrer\" tout en bas de la carte pour valider le changement.</li>"
            "</ol>"
            "<p>Si les deux saisies ne correspondent pas exactement, un message d'erreur s'affiche et rien n'est modifié : "
            "recommencez simplement la saisie depuis le début. Un mot de passe d'au moins 8 caractères est exigé ; un mot de passe "
            "plus long (par exemple une phrase entière) et varié (majuscules, minuscules, chiffres, caractères spéciaux) reste "
            "toujours recommandé, même si techniquement facultatif. <strong>Important</strong> : changer votre mot de passe vous "
            "déconnecte automatiquement de tous vos autres appareils et navigateurs déjà connectés, pour votre sécurité — vous "
            "resterez connecté uniquement sur l'appareil et le navigateur depuis lequel vous venez d'effectuer le changement.</p>"

            "<h2>Paramètres du navigateur</h2>"
            "<p>Cette dernière section du profil ne concerne que l'appareil et le navigateur que vous utilisez actuellement — "
            "rien n'est envoyé au serveur, et rien n'est partagé avec vos autres appareils.</p>"
            "<ul>"
            "<li><strong>Langue</strong> : français ou anglais pour l'instant. Cliquez sur le menu déroulant, choisissez la langue "
            "souhaitée : le changement s'applique immédiatement (la page se recharge automatiquement dans la nouvelle langue), sans "
            "bouton supplémentaire à cliquer, et reste mémorisé pour vos prochaines visites depuis ce même navigateur.</li>"
            "<li><strong>Thème</strong> : clair, sombre, ou système (suit automatiquement le réglage de votre appareil). Cliquez sur "
            "le menu déroulant et choisissez l'option voulue : le changement s'applique instantanément, sans recharger la page. "
            "Ce réglage ne concerne que les couleurs neutres de l'interface (fonds, cartes, bordures) — pas les couleurs de marque "
            "du portail, qui restent identiques dans les deux cas.</li>"
            "</ul>"

            "<h2>Pied de page</h2>"
            "<p>Présent en bas de chaque page (sauf la page de connexion) : liens vers cette page de Documentation, vers la page "
            "Support, et vers l'interface d'administration du système (réservée aux comptes administrateurs — si vous n'avez pas "
            "les droits nécessaires, le système vous le signalera directement). Le numéro de version du portail et le nom de BYRTN "
            "y figurent également.</p>"

            "<h2>Se déconnecter</h2>"
            "<p>Cliquez sur le bouton \"Déconnexion\", toujours visible en haut à droite de chaque page. Votre session se termine "
            "immédiatement et vous êtes ramené à la page de connexion — vous devrez ressaisir votre identifiant et votre mot de "
            "passe pour vous reconnecter. Si plusieurs onglets d'applications étaient encore ouverts au moment de la déconnexion, "
            "ils cessent également d'être accessibles dès que vous tentez d'y recharger une page ou d'y naviguer.</p>"
        ),
        "en": (
            "<h2>What is Wappos?</h2>"
            "<p>Wappos is a turnkey server product designed by <strong>BYRTN</strong>, a digital sovereignty integrator. "
            "Its goal: letting a company take back control of its everyday data and digital tools "
            "(files, email, calendar, office suite, management, business apps...) by hosting them itself, on its own server, "
            "rather than depending on monthly subscriptions to large cloud providers (Microsoft, Google...). "
            "Fewer subscriptions, more autonomy, an infrastructure that truly belongs to the company using it.</p>"

            "<h2>How Wappos is built</h2>"
            "<p>Wappos is built on YunoHost, an open-source server operating system that serves as the base of "
            "the whole Wappos system. This base handles user accounts, single sign-on, security "
            "certificates (HTTPS), backups, and a catalog of ready-to-install applications. On top of that base, BYRTN built "
            "<strong>Docker Gate</strong>, an in-house tool that makes it easy to add extra applications packaged with Docker, even "
            "when they don't exist natively for the system — without ever duplicating account or security management, which "
            "always stays entirely handled by the system. Finally, the portal you are currently using, <strong>Wappos Portal</strong>, "
            "is an in-house interface built by BYRTN on top of the system: a simplified, custom-branded view of your applications "
            "and account settings, designed to be easier to use day-to-day than the standard technical interface of a self-hosted "
            "server — while relying, behind the scenes, on the very same security and authentication mechanisms as the system "
            "itself. In practice, whenever you log in, change your password, or add an email alias, it is always the system that "
            "verifies and applies the request — this portal never runs its own parallel account management.</p>"

            "<h2>Single sign-on (SSO)</h2>"
            "<p>The system centralizes every user account in a single LDAP directory — a database specialized in securely storing "
            "accounts and passwords, a standard widely used in professional infrastructures. In practice, for you, this means "
            "<strong>single sign-on</strong> (often shortened to SSO): one username and one password are enough to access every "
            "application installed on the system, without having to log in separately to each one, and without having to remember "
            "a different password per tool. As long as your session stays active in your browser, you move freely from one "
            "application to another, and from the portal to an application and back, without ever being asked for your credentials "
            "again in between.</p>"

            "<h2>What this portal is for</h2>"
            "<p>Wappos Portal is your single, everyday entry point to the applications installed on this server, and to your own "
            "account settings. You don't need to know anything about the system or Docker Gate to use it: everything below covers, "
            "step by step, every feature you can use directly from this portal.</p>"

            "<h2>Logging in</h2>"
            "<p>The login page asks for your account name and password — the same credentials created or given to you by your "
            "server's administrator. Click the \"Account name\" field, type your username, then click the \"Password\" field (or "
            "press the Tab key to jump straight to it) and type your password. Finally click the \"Log in\" button (or press "
            "Enter) to confirm. Once logged in, you stay authenticated as long as your session remains valid (until you log out "
            "explicitly, or your session expires depending on the server's configuration) — you don't need to re-enter your "
            "credentials on every new page or application, thanks to the single sign-on described above.</p>"

            "<h2>The home page</h2>"
            "<p>Once logged in, the home page shows one tile per application you have access to (access to each application is "
            "decided by the administrator, through the system's permissions — this portal simply displays what the system allows "
            "you to see).</p>"

            "<h3>Opening an app</h3>"
            "<ol>"
            "<li>Click once on the tile of the app you want.</li>"
            "<li>A new browser tab opens automatically with the requested app — your portal stays displayed unchanged in the "
            "original tab, still open behind it.</li>"
            "<li>Use the app normally in that new tab, like any other website.</li>"
            "<li>Once you're done, simply close that tab (click the small \"×\" on the tab, or use the keyboard shortcut Ctrl+W on "
            "Windows/Linux, Cmd+W on Mac) to go straight back to the portal's tab, which stayed open and logged in the whole "
            "time — you don't need to log back in to anything.</li>"
            "</ol>"
            "<p>You can also keep several apps open at the same time, each in its own tab, and move freely between them and the "
            "portal: click directly on the tab you want at the top of your browser, or use Ctrl+Tab (Cmd+Option+Right Arrow on "
            "Mac) to move to the next tab, Ctrl+Shift+Tab to go back to the previous one. Closing an app's tab never logs out your "
            "session nor any other open tab.</p>"

            "<h3>Reordering tiles</h3>"
            "<p>Click a tile and hold the click down (the cursor usually changes shape), drag it to where you want it among the "
            "other tiles, then release the click to drop it in its new spot. The order you choose is remembered for you "
            "individually: each user on the server can have their own order, without affecting anyone else's.</p>"

            "<h3>Filtering apps</h3>"
            "<p>Click the search field above the tiles, then type one or more words from the app's name. Matching tiles stay "
            "visible, the rest hide immediately as you type, with no page reload. Clear the text you typed (or reload the page) "
            "to show every tile again.</p>"

            "<h3>Searching the web</h3>"
            "<p>If the administrator has configured a default search engine for your domain, a second search bar is available "
            "above the tiles. Click it, type your search, then confirm with Enter or by clicking the magnifying-glass button: the "
            "results open directly in a new tab, just like an app, leaving your portal untouched in the original tab.</p>"

            "<h2>Editing your profile</h2>"
            "<p>Accessible by clicking the pencil icon next to your name, at the top of the page, or via the \"Back to portal\" "
            "link then the pencil icon. The page is organized into several independent blocks, each with its own save action "
            "(changing your name, for example, has no effect on your password, and vice versa).</p>"

            "<h3>Personal information</h3>"
            "<ul>"
            "<li><strong>Full name</strong>: freely editable, this is the name shown in the portal's header.</li>"
            "<li><strong>Primary email address</strong>: shown read-only (greyed out) on this server — changing it is reserved to "
            "the administrator. Marked with an asterisk and its explanatory note.</li>"
            "<li><strong>Username</strong>: never editable, on any server — it is your account's unique identifier, used to "
            "authenticate you. Marked with the same asterisk.</li>"
            "</ul>"
            "<p>To change your full name: click the \"Full name\" field, clear the existing text if needed, type the new name, "
            "then click the \"Save\" button at the bottom of the card to confirm the change.</p>"

            "<h3>Email addresses (aliases)</h3>"
            "<p>An alias is an extra address that receives mail in the same place as your primary address — useful, for example, "
            "to receive mail on both <em>firstname.lastname@domain</em> and <em>contact@domain</em>.</p>"
            "<p><strong>Adding an alias</strong>: click the input field provided for it, type the new full address, then click the "
            "\"Add\" button right next to it — the alias then appears immediately in the list above. <strong>Removing an alias</strong>: "
            "click the \"Remove\" link shown next to the address in the list; removal is immediate, with no further confirmation "
            "at this time.</p>"

            "<h3>Email forwarding addresses</h3>"
            "<p>A forwarding address sends a copy of your mail to another mailbox (external or internal) — useful if you also "
            "check your mail elsewhere. Adding and removing works exactly the same way as for aliases, described just above.</p>"

            "<h3>Change password</h3>"
            "<ol>"
            "<li>Click the \"New password\" field and type your new password.</li>"
            "<li>If you want to check what you just typed, click the \"Show\" link to the right of the field: your entry then "
            "appears in plain text (the link becomes \"Hide\", click it again to hide the entry once more).</li>"
            "<li>Click the \"Confirm new password\" field and type the exact same password again.</li>"
            "<li>Click the \"Save\" button at the bottom of the card to confirm the change.</li>"
            "</ol>"
            "<p>If the two entries don't match exactly, an error message appears and nothing is changed: simply start over. A "
            "password of at least 8 characters is required; a longer password (e.g. a whole passphrase) and a varied one "
            "(uppercase, lowercase, digits, special characters) is always recommended, even though technically optional. "
            "<strong>Important</strong>: changing your password automatically logs you out of all your other already-connected "
            "devices and browsers, for your security — you'll stay logged in only on the device and browser you just made the "
            "change from.</p>"

            "<h2>Browser settings</h2>"
            "<p>This last section of the profile only concerns the device and browser you're currently using — nothing is sent "
            "to the server, and nothing is shared with your other devices.</p>"
            "<ul>"
            "<li><strong>Language</strong>: French or English for now. Click the dropdown, choose the language you want: the "
            "change applies immediately (the page reloads automatically in the new language), no extra button to click, and stays "
            "remembered for your next visits from this same browser.</li>"
            "<li><strong>Theme</strong>: light, dark, or system (automatically follows your device's own setting). Click the "
            "dropdown and pick the option you want: the change applies instantly, with no page reload. This setting only affects "
            "the interface's neutral colors (backgrounds, cards, borders) — not the portal's brand colors, which stay identical "
            "either way.</li>"
            "</ul>"

            "<h2>Footer</h2>"
            "<p>Present at the bottom of every page (except the login page): links to this Documentation page, to the Support "
            "page, and to the system's administration interface (reserved to administrator accounts — if you don't have the "
            "required rights, the system will tell you directly). The portal's version number and BYRTN's name are shown there too.</p>"

            "<h2>Logging out</h2>"
            "<p>Click the \"Log out\" button, always visible in the top right corner of every page. Your session ends immediately "
            "and you're taken back to the login page — you'll need to re-enter your username and password to log back in. If "
            "several app tabs were still open at the moment you logged out, they also stop being accessible as soon as you try to "
            "reload or navigate within them.</p>"
        ),
    },

    "page_body_support_faq": {
        "fr": (
            "<h2>Questions fréquentes</h2>"

            "<h3>J'ai oublié mon mot de passe, que faire ?</h3>"
            "<p>Ce portail ne propose pas de réinitialisation de mot de passe en autonomie à ce jour. Contactez l'administrateur "
            "de votre serveur (voir plus bas) : lui seul peut réinitialiser un mot de passe depuis l'interface d'administration.</p>"

            "<h3>Je ne vois pas toutes les applications installées sur le serveur, est-ce normal ?</h3>"
            "<p>Oui. L'accès à chaque application est décidé par l'administrateur, application par application et utilisateur par "
            "utilisateur. Si vous pensez avoir besoin d'accéder à une application que vous ne voyez pas, contactez l'administrateur.</p>"

            "<h3>Puis-je changer mon adresse mail principale moi-même ?</h3>"
            "<p>Non, pas sur ce serveur : ce champ est volontairement réservé à l'administrateur. Vous pouvez en revanche ajouter "
            "librement des alias et des adresses de transfert depuis votre profil (voir la Documentation).</p>"

            "<h3>Le changement de mot de passe m'a déconnecté de mes autres appareils, est-ce normal ?</h3>"
            "<p>Oui, c'est un comportement automatique et volontaire, pour votre sécurité : impossible à désactiver, il se produit "
            "systématiquement à chaque changement de mot de passe.</p>"

            "<h3>L'ordre de mes tuiles suit-il mon compte, ou est-il propre à chaque appareil ?</h3>"
            "<p>Il suit votre compte : réorganisez vos tuiles une fois, et vous retrouverez le même ordre en vous connectant depuis "
            "un autre appareil ou un autre navigateur.</p>"

            "<h3>La langue ou le thème que j'ai choisi a disparu sur un autre appareil, est-ce normal ?</h3>"
            "<p>Oui — contrairement à l'ordre des tuiles, la langue et le thème sont des préférences propres à chaque navigateur, "
            "pas à votre compte. Vous devez les régler séparément sur chaque appareil que vous utilisez.</p>"

            "<h3>Comment me déconnecter de tous mes appareils en une seule fois ?</h3>"
            "<p>Changez votre mot de passe depuis votre profil : cela vous déconnecte automatiquement de tous vos autres appareils "
            "et navigateurs, sans action supplémentaire à faire.</p>"

            "<h3>Le portail s'affiche différemment sur mon téléphone ou ma tablette, est-ce un bug ?</h3>"
            "<p>Non, c'est voulu : la présentation s'adapte à la taille de l'écran (colonnes empilées sur petit écran, par exemple) "
            "pour rester utilisable sur mobile et tablette.</p>"

            "<h3>Puis-je changer mon nom d'utilisateur ?</h3>"
            "<p>Non, jamais, sur aucun serveur : c'est l'identifiant unique et permanent de votre compte.</p>"
        ),
        "en": (
            "<h2>Frequently asked questions</h2>"

            "<h3>I forgot my password, what should I do?</h3>"
            "<p>This portal doesn't offer self-service password reset at this time. Contact your server's administrator (see "
            "below): only they can reset a password from the administration interface.</p>"

            "<h3>I don't see every application installed on the server, is that normal?</h3>"
            "<p>Yes. Access to each application is decided by the administrator, application by application and user by user. If "
            "you think you need access to an application you don't see, contact the administrator.</p>"

            "<h3>Can I change my primary email address myself?</h3>"
            "<p>No, not on this server: this field is deliberately reserved to the administrator. You can however freely add "
            "aliases and forwarding addresses from your profile (see the Documentation).</p>"

            "<h3>Changing my password logged me out of my other devices, is that normal?</h3>"
            "<p>Yes, this is an automatic and deliberate behavior, for your security: it can't be disabled, and happens every time "
            "a password is changed.</p>"

            "<h3>Does my tile order follow my account, or is it specific to each device?</h3>"
            "<p>It follows your account: reorder your tiles once, and you'll find the same order when logging in from another "
            "device or browser.</p>"

            "<h3>The language or theme I chose disappeared on another device, is that normal?</h3>"
            "<p>Yes — unlike tile order, language and theme are preferences specific to each browser, not to your account. You "
            "need to set them separately on each device you use.</p>"

            "<h3>How do I log out of all my devices at once?</h3>"
            "<p>Change your password from your profile: this automatically logs you out of all your other devices and browsers, "
            "with nothing extra to do.</p>"

            "<h3>The portal looks different on my phone or tablet, is that a bug?</h3>"
            "<p>No, it's intentional: the layout adapts to the screen size (e.g. stacked columns on a small screen) to stay usable "
            "on mobile and tablet.</p>"

            "<h3>Can I change my username?</h3>"
            "<p>No, never, on any server: it is your account's unique and permanent identifier.</p>"
        ),
    },

    "h2_contact_admin": {"fr": "Vous avez une autre question ?", "en": "Have another question?"},
    "contact_admin_intro": {
        "fr": "Contactez l'administrateur de votre serveur :",
        "en": "Contact your server's administrator:",
    },
    "btn_reveal_admin_email": {
        "fr": "Contacter l'administrateur",
        "en": "Contact the administrator",
    },
    "h2_contact_editor": {"fr": "Vous souhaitez en savoir plus sur Wappos ?", "en": "Want to know more about Wappos?"},
    "contact_editor_intro": {
        "fr": "Contactez l'éditeur, BYRTN :",
        "en": "Contact the publisher, BYRTN:",
    },
    "contact_form_name_label": {"fr": "Votre nom et prénom", "en": "Your name"},
    "contact_form_name_placeholder": {"fr": "Prénom NOM", "en": "First name LAST NAME"},
    "contact_form_email_label": {"fr": "Votre adresse mail", "en": "Your email address"},
    "contact_form_email_placeholder": {"fr": "vous@votre-entreprise.fr", "en": "you@yourcompany.com"},
    "contact_form_message_label": {"fr": "Votre message", "en": "Your message"},
    "contact_form_message_placeholder": {
        "fr": "Décrivez votre question ou votre besoin en quelques lignes...",
        "en": "Describe your question or your need in a few lines...",
    },
    "contact_form_rgpd_label": {
        "fr": "J'accepte que mes données soient utilisées uniquement pour répondre à ma demande, dans le respect du RGPD.",
        "en": "I agree that my data will only be used to respond to my request, in compliance with GDPR.",
    },
    "btn_send": {"fr": "Envoyer le message", "en": "Send message"},
    "msg_contact_sent": {
        "fr": "Message envoyé, merci — l'éditeur reviendra vers vous directement par email.",
        "en": "Message sent, thank you — the publisher will get back to you directly by email.",
    },
    "err_contact_missing_fields": {
        "fr": "Merci de remplir tous les champs et de cocher la case RGPD.",
        "en": "Please fill in every field and check the GDPR box.",
    },
    "err_contact_send_failed": {
        "fr": "Impossible d'envoyer le message pour l'instant, réessaie plus tard.",
        "en": "Unable to send the message right now, try again later.",
    },

    "err_api_unreachable": {
        "fr": "Impossible de contacter l'API Wappos, réessaie dans un instant.",
        "en": "Unable to reach the Wappos API, try again in a moment.",
    },
    "msg_profile_updated": {"fr": "Profil mis à jour.", "en": "Profile updated."},
    "err_password_mismatch": {
        "fr": "Les deux mots de passe ne correspondent pas.",
        "en": "The two passwords don't match.",
    },
    "err_invalid_current_password": {
        "fr": "Mot de passe actuel incorrect.",
        "en": "Current password is incorrect.",
    },
    "msg_password_updated": {"fr": "Mot de passe mis à jour.", "en": "Password updated."},
    "err_action_failed": {"fr": "La modification a échoué.", "en": "The change failed."},
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
