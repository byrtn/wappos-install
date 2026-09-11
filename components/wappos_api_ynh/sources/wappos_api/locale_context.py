# Auteur : Patrick Ritaine

import contextvars

DEFAULT_LOCALE = "en"
SUPPORTED_LOCALES = ("en", "fr")

_locale_var: contextvars.ContextVar[str] = contextvars.ContextVar("wappos_locale", default=DEFAULT_LOCALE)


def normalize_locale(locale: str | None) -> str:
    if locale and locale.lower() in SUPPORTED_LOCALES:
        return locale.lower()
    return DEFAULT_LOCALE


def set_locale(locale: str | None) -> None:
    _locale_var.set(normalize_locale(locale))


def get_locale() -> str:
    return _locale_var.get()
