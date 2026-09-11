DEFAULT_LANG = "en"
LANGS = ("fr", "en")

STRINGS = {
    "page_title": {"fr": "Wappos — Configuration initiale", "en": "Wappos — Initial setup"},
    "subtitle": {"fr": "Configuration initiale", "en": "Initial setup"},
    "loading_title": {"fr": "Configuration de Wappos en cours...", "en": "Setting up Wappos..."},
    "progress_title": {"fr": "Installation de Wappos", "en": "Installing Wappos"},
    "progress_intro": {"fr": "Configuration enregistrée. L'installation se poursuit automatiquement ci-dessous — vous pouvez laisser cette page ouverte, aucune action requise.", "en": "Configuration saved. Installation continues automatically below — you can leave this page open, no action needed."},
    "progress_done_title": {"fr": "Wappos est installé et configuré.", "en": "Wappos is installed and configured."},
    "progress_done_text": {"fr": "Vous pouvez maintenant vous connecter.", "en": "You can now log in."},
    "btn_go_to_portal": {"fr": "Ouvrir le portail Wappos", "en": "Open the Wappos portal"},
    "progress_failed_title": {"fr": "Une erreur est survenue pendant l'installation.", "en": "An error occurred during installation."},
    "progress_failed_text": {"fr": "Le détail complet est visible ci-dessous.", "en": "Full details are shown below."},
    "loading_subtext": {"fr": "Cela peut prendre plusieurs minutes, merci de patienter sans recharger ni fermer cette page.", "en": "This can take several minutes, please wait without reloading or closing this page."},
    "placeholder_domain": {"fr": "exemple.local", "en": "example.local"},
    "hint_domain": {"fr": "C'est l'adresse à laquelle vous accéderez à Wappos (ex. https://exemple.local). Vous pourrez gérer d'autres domaines plus tard depuis l'administration.", "en": "This is the address you'll use to access Wappos (e.g. https://example.local). You can manage other domains later from the administration panel."},
    "hint_username": {"fr": "Ce sera votre compte administrateur Wappos. Lettres, chiffres et underscore uniquement.", "en": "This will be your Wappos administrator account. Letters, digits and underscore only."},
    "btn_show": {"fr": "Afficher", "en": "Show"},
    "btn_hide": {"fr": "Masquer", "en": "Hide"},
    "hint_password": {"fr": "Un mot de passe robuste, évitez les mots courants.", "en": "A strong password, avoid common words."},
    "btn_configure": {"fr": "Configurer Wappos", "en": "Configure Wappos"},
    "err_domain_empty": {"fr": "Le nom de domaine ne peut pas etre vide.", "en": "The domain name cannot be empty."},
    "err_username_invalid": {"fr": "L'identifiant ne peut contenir que des lettres, chiffres et underscore.", "en": "The username can only contain letters, digits and underscore."},
    "err_passwords_mismatch": {"fr": "Les mots de passe ne correspondent pas ou sont vides.", "en": "The passwords do not match or are empty."},
    "err_password_too_short": {"fr": "Le mot de passe doit contenir au moins 8 caracteres.", "en": "The password must contain at least 8 characters."},
    "err_password_too_similar": {"fr": "Le mot de passe ne peut pas etre identique a l'identifiant, au nom ou au domaine.", "en": "The password cannot be identical to the username, name, or domain."},
    "err_unknown_setup_failure": {"fr": "Echec inconnu de la configuration.", "en": "Unknown setup failure."},
    "default_fullname": {"fr": "Administrateur", "en": "Administrator"},
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
