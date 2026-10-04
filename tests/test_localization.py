import ast
import datetime
import unittest
from pathlib import Path
from string import Formatter
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import flet as ft

from components.app_bar import AppBar
from components.settings_group import SettingsGroup
from components.task_item import TaskItem
from core.defs.tasks import TaskError, TaskInfo
from core.downloads_manager import DownloadManager
from localization import (
    LANGUAGE_KEY,
    SUPPORTED_LANGUAGES,
    Localizer,
    catalog,
    initialize_localization,
    system_language,
)
from pages.auth_management import AuthManagementPage
from pages.download_image_by_link import DownloadImageByLinkPage
from pages.download_post import DownloadPostPage
from pages.download_several_posts import DownloadSeveralPostsPage
from pages.downloads_center import DownloadsCenterPage
from pages.feedback_and_bugs import FeedbackAndBugsPage
from pages.merge_author_content import MergeAuthorContentPage
from pages.settings_page import SettingsPage
from pages.welcome_page import WelcomePage


class LocalizationTests(unittest.TestCase):
    def test_system_language_uses_primary_language_and_english_fallback(self):
        for locales, expected in (
            ([ft.Locale("ru", "RU")], "ru"),
            ([ft.Locale("ru", "BY")], "ru"),
            ([ft.Locale("en", "GB")], "en"),
            ([ft.Locale("de"), ft.Locale("ru")], "en"),
            ([], "en"),
        ):
            self.assertEqual(system_language(locales), expected)

    def test_catalogs_have_complete_keys_and_matching_named_placeholders(self):
        english, russian = catalog("en"), catalog("ru")
        self.assertEqual(set(english), set(russian))
        formatter = Formatter()

        def placeholders(message):
            return {name for _, name, _, _ in formatter.parse(message) if name}

        for key, source in english.items():
            with self.subTest(message=key):
                translated = russian[key]
                if isinstance(source, str):
                    self.assertTrue(translated)
                    self.assertEqual(placeholders(source), placeholders(translated))
                elif isinstance(source, dict):
                    self.assertEqual(set(source), {"one", "other"})
                    self.assertEqual(set(translated), {"one", "few", "many"})
                    for form in translated.values():
                        self.assertEqual(
                            placeholders(source["other"]), placeholders(form)
                        )
                else:
                    self.assertEqual(len(source), 12)
                    self.assertEqual(len(translated), 12)

        for file in Path("src").rglob("*.py"):
            for call in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
                if not isinstance(call, ast.Call) or not call.args:
                    continue
                function = call.func
                if (
                    isinstance(function, ast.Attribute)
                    and function.attr in ("tr", "plural")
                    or isinstance(function, ast.Name)
                    and function.id == "tr"
                ):
                    message = call.args[0]
                    if isinstance(message, ast.Constant) and isinstance(
                        message.value, str
                    ):
                        self.assertIn(
                            message.value, english, f"Missing translation in {file}"
                        )

    def test_russian_plural_rules_and_dates_do_not_depend_on_host_locale(self):
        ru, en = Localizer("ru"), Localizer("en")
        for count, expected in (
            (0, "0 дней"),
            (1, "1 день"),
            (2, "2 дня"),
            (5, "5 дней"),
            (11, "11 дней"),
            (12, "12 дней"),
            (14, "14 дней"),
            (21, "21 день"),
            (22, "22 дня"),
            (25, "25 дней"),
            (101, "101 день"),
            (111, "111 дней"),
        ):
            self.assertEqual(ru.plural("count.days", count), expected)
        self.assertEqual(en.plural("count.days", 1), "1 day")
        self.assertEqual(en.plural("count.days", 2), "2 days")
        date = datetime.date(2026, 10, 4)
        self.assertEqual(ru.format_date(date), "04 окт. 2026")
        self.assertEqual(en.format_date(date), "04 Oct 2026")
        self.assertEqual(ru.t("Missing {value}", value="fallback"), "Missing fallback")

    def test_pages_and_shared_components_use_session_language(self):
        ru, en = Localizer("ru"), Localizer("en")
        manager = DownloadManager()
        for cls in (
            WelcomePage,
            SettingsPage,
            DownloadPostPage,
            DownloadSeveralPostsPage,
            DownloadImageByLinkPage,
            MergeAuthorContentPage,
            DownloadsCenterPage,
            AuthManagementPage,
            FeedbackAndBugsPage,
        ):
            with self.subTest(page=cls.__name__):
                view = cls(manager, localizer=ru)
                self.assertIs(view.localizer, ru)
                toolbar = (
                    view.toolbar
                    if hasattr(view, "toolbar")
                    else view.controls[0].content.controls[0]
                )
                self.assertEqual(toolbar.home_button.content, "Главная")
                self.assertEqual(toolbar.settings_button.content, "Настройки")
                if cls != WelcomePage:
                    shell = view.controls[0]
                    footer_action = shell.content.controls[-1].content.controls[-1]
                    self.assertEqual(
                        footer_action.content,
                        (
                            "Проект на GitHub"
                            if cls == FeedbackAndBugsPage
                            else "Обратная связь"
                        ),
                    )
        self.assertEqual(AppBar(manager, localizer=en).home_button.content, "Home")
        self.assertEqual(AppBar(manager, localizer=ru).home_button.content, "Главная")
        settings = SettingsGroup(localizer=ru)
        self.assertEqual(settings.language_dropdown.value, "ru")
        self.assertEqual(settings.retry_button.content, "Повторить")
        self.assertFalse(hasattr(settings, "save_button"))
        self.assertEqual(
            [option.key for option in settings.language_dropdown.options],
            list(SUPPORTED_LANGUAGES),
        )
        posts = DownloadSeveralPostsPage(manager, localizer=ru)
        posts.set_range(datetime.date(2026, 1, 1), datetime.date(2026, 1, 2))
        posts.update_ranges()
        self.assertEqual(posts.range_note.value, "2 дня · Обе даты включены")
        self.assertEqual(posts.date_from_text.value, "01 янв. 2026")

    def test_task_status_metadata_and_backend_errors_are_translated_at_render(self):
        info = TaskInfo(
            percent=0,
            title="Original post title",
            author="Original author",
            post_id="post",
            path="",
            finished=True,
            count_files=21,
            total_weight=1024**2,
            error=TaskError.ACCESS_DENIED,
        )
        ru = Localizer("ru")
        task = TaskItem(info, visible=True, localizer=ru)
        self.assertEqual(task.task_name.value, "Original post title")
        self.assertIn("Original author", task.task_metadata.value)
        self.assertIn("21 файл", task.task_metadata.value)
        self.assertIn("МБ", task.task_metadata.value)
        self.assertEqual(task.detail.value, "Нет доступа к посту")
        self.assertEqual(task.status.value, "Ошибка")
        self.assertEqual(task.retry_button.content, "Повторить")
        ru.set_language("en")
        task.update_view(info, visible=True)
        self.assertEqual(task.status.value, "Failed")
        self.assertEqual(task.detail.value, "Don't have access to post")


class LanguageInitializationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.preferences = SimpleNamespace(
            get=AsyncMock(return_value=None), set=AsyncMock(return_value=True)
        )
        self.page = SimpleNamespace(
            get_device_info=AsyncMock(
                return_value=SimpleNamespace(locales=[ft.Locale("ru", "RU")])
            )
        )
        patcher = patch(
            "localization.ft.SharedPreferences", return_value=self.preferences
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch("localization.logger")
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_first_launch_uses_device_language_and_persists_it(self):
        localizer = await initialize_localization(self.page)
        self.assertEqual(localizer.language, "ru")
        self.preferences.set.assert_awaited_once_with(LANGUAGE_KEY, "ru")
        self.assertEqual(
            self.page.locale_configuration.current_locale.language_code, "ru"
        )
        self.assertEqual(
            [
                locale.language_code
                for locale in self.page.locale_configuration.supported_locales
            ],
            ["en", "ru"],
        )

    async def test_saved_language_wins_over_system_and_does_not_get_rewritten(self):
        for language in SUPPORTED_LANGUAGES:
            self.preferences.get.return_value = language
            localizer = await initialize_localization(self.page)
            self.assertEqual(localizer.language, language)
        self.page.get_device_info.assert_not_awaited()
        self.preferences.set.assert_not_awaited()

    async def test_unsupported_system_language_and_missing_locales_use_english(self):
        for locales in ([ft.Locale("de"), ft.Locale("ru")], []):
            self.page.get_device_info.return_value.locales = locales
            localizer = await initialize_localization(self.page)
            self.assertEqual(localizer.language, "en")

    async def test_failed_device_service_still_starts_in_english(self):
        self.page.get_device_info.side_effect = RuntimeError("unavailable")
        localizer = await initialize_localization(self.page)
        self.assertEqual(localizer.language, "en")
        self.preferences.set.assert_awaited_once_with(LANGUAGE_KEY, "en")

    async def test_invalid_saved_language_is_repaired_without_system_override(self):
        self.preferences.get.return_value = "deleted-language"
        localizer = await initialize_localization(self.page)
        self.assertEqual(localizer.language, "en")
        self.page.get_device_info.assert_not_awaited()
        self.preferences.set.assert_awaited_once_with(LANGUAGE_KEY, "en")

    async def test_first_run_storage_failure_does_not_prevent_startup(self):
        self.preferences.set.side_effect = OSError("unavailable")
        self.assertEqual((await initialize_localization(self.page)).language, "ru")
        self.preferences.set.side_effect = None
        self.preferences.set.return_value = False
        self.assertEqual((await initialize_localization(self.page)).language, "ru")
