"""Per-session UI translations and Flet locale configuration.

English messages are catalog IDs, following gettext's source-message convention.
Keep placeholders named so translators can reorder them without changing Python.
"""

import json
import logging
from functools import cache
from pathlib import Path

import flet as ft

LANGUAGE_KEY = "current-app-language"
SUPPORTED_LANGUAGES = {"en": "🇬🇧 English", "ru": "🇷🇺 Русский"}
logger = logging.getLogger(__name__)


@cache
def catalog(language):
    return json.loads(
        (Path(__file__).with_name("locales") / f"{language}.json").read_text(
            encoding="utf-8"
        )
    )


class Localizer:
    def __init__(self, language="en"):
        self.set_language(language)

    def set_language(self, language):
        self.language = language if language in SUPPORTED_LANGUAGES else "en"

    def t(self, message, **values):
        translated = catalog(self.language).get(message, message)
        return translated.format(**values) if values else translated

    def plural(self, message, count, **values):
        if self.language == "ru":
            remainder = abs(count) % 100
            form = (
                "one"
                if remainder % 10 == 1 and remainder != 11
                else (
                    "few"
                    if 2 <= remainder % 10 <= 4 and not 12 <= remainder <= 14
                    else "many"
                )
            )
        else:
            form = "one" if count == 1 else "other"
        forms = catalog(self.language)[message]
        return forms[form].format(count=count, **values)

    def format_date(self, value):
        months = catalog(self.language)["date.months"]
        return f"{value.day:02d} {months[value.month - 1]} {value.year}"

    def configure_page(self, page):
        page.locale_configuration = ft.LocaleConfiguration(
            supported_locales=[ft.Locale(language) for language in SUPPORTED_LANGUAGES],
            current_locale=ft.Locale(self.language),
        )


def system_language(locales):
    if not locales:
        return "en"
    language = locales[0].language_code.lower().replace("_", "-").split("-")[0]
    return language if language in SUPPORTED_LANGUAGES else "en"


async def initialize_localization(page):
    preferences = ft.SharedPreferences()
    saved_language = await preferences.get(LANGUAGE_KEY)
    if saved_language is None:
        try:
            language = system_language((await page.get_device_info()).locales)
        except Exception:
            logger.exception("Could not determine the system language; using English")
            language = "en"
    else:
        language = saved_language if saved_language in SUPPORTED_LANGUAGES else "en"
    if saved_language != language:
        try:
            if await preferences.set(LANGUAGE_KEY, language) is False:
                raise OSError("Could not store the initial language")
        except Exception:
            logger.exception("Could not save the initial language")
    localizer = Localizer(language)
    localizer.configure_page(page)
    return localizer
