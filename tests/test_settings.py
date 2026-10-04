import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import flet as ft

from components.settings_group import SettingsGroup
from core.download_limiter import DownloadLimiter
from core.downloads_manager import DownloadManager


class SettingsTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.storage = {"current-app-theme": "light"}
        self.preferences = Mock()
        self.preferences.get = AsyncMock(side_effect=self.storage.get)

        async def store(key, value):
            self.storage[key] = value
            return True

        async def remove(key):
            self.storage.pop(key, None)
            return True

        self.preferences.set = AsyncMock(side_effect=store)
        self.preferences.remove = AsyncMock(side_effect=remove)
        self.patchers = [
            patch(
                "components.settings_group.ft.SharedPreferences",
                return_value=self.preferences,
            ),
            patch("components.settings_group.logger"),
            patch(
                "components.settings_group.get_download_settings",
                new=AsyncMock(
                    return_value=SimpleNamespace(
                        downloads_folder="/custom/downloads",
                        need_download_photos=True,
                        need_download_videos=True,
                        need_download_audios=False,
                        need_download_files=True,
                        chunk_size=153600,
                        download_timeout=3600,
                        max_parallelism=5,
                        preferred_video_size="full_hd",
                        post_text_format="md",
                    )
                ),
            ),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.manager = DownloadManager()
        self.form = SettingsGroup(self.manager)
        self.form.update = Mock()
        self.form.host_page = SimpleNamespace(
            theme_mode=ft.ThemeMode.LIGHT, update=Mock(), schedule_update=Mock()
        )
        await self.form.set_initial_values()

    async def asyncTearDown(self):
        self.form.active = False
        await self.form.flush_pending_saves()

    async def change(self, control, value):
        control.value = value
        await self.form.save_control(SimpleNamespace(control=control))

    def type_value(self, field, value):
        field.value = value
        self.form.schedule_text_save(SimpleNamespace(control=field))

    async def test_loading_does_not_write_and_save_button_is_removed(self):
        self.assertEqual(self.form.folder, "/custom/downloads")
        self.assertEqual(self.form.max_parallelism_textfield.value, "5")
        self.assertEqual(self.form.download_timeout_textfield.value, "3600")
        self.assertEqual(self.form.theme_picker.value, "light")
        self.assertFalse(self.form.switch_download_audios.value)
        self.assertFalse(hasattr(self.form, "save_button"))
        self.assertEqual(self.form.save_delay, 2)
        self.preferences.set.assert_not_awaited()

    async def test_discrete_controls_save_only_the_changed_setting_immediately(self):
        await self.change(self.form.switch_download_videos, False)
        self.preferences.set.assert_awaited_once_with("need-download-videos", "False")
        self.assertTrue(self.form.video_size_dropdown.disabled)
        await self.change(self.form.post_text_format_dropdown, "raw")
        await self.change(self.form.video_size_dropdown, "high")
        self.assertEqual(self.storage["post-text-format"], "raw")
        self.assertEqual(self.storage["preferred-video-size"], "high")
        self.assertFalse(self.form.switch_download_videos.disabled)
        self.assertEqual(self.form.status_text.value, "Changes saved.")

    async def test_theme_applies_and_persists_immediately(self):
        await self.form.theme_picker.select("dark")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.DARK)
        self.assertEqual(self.storage["current-app-theme"], "dark")
        await self.form.theme_picker.select("light")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.LIGHT)
        self.assertEqual(self.storage["current-app-theme"], "light")

    async def test_folder_cancel_does_not_save_and_selection_saves_immediately(self):
        with patch("components.settings_group.ft.FilePicker") as picker:
            picker.return_value.get_directory_path = AsyncMock(return_value=None)
            await self.form.pick_download_folder()
            self.preferences.set.assert_not_awaited()
            picker.return_value.get_directory_path.return_value = "/custom/new-folder"
            await self.form.pick_download_folder()
        self.preferences.set.assert_awaited_once_with(
            "download-folder", "/custom/new-folder"
        )

    async def test_typing_waits_and_restarts_the_two_second_timer(self):
        entered, release = asyncio.Event(), asyncio.Event()

        async def delay(seconds):
            self.assertEqual(seconds, 2)
            entered.set()
            await release.wait()

        with patch("components.settings_group.asyncio.sleep", new=delay):
            self.type_value(self.form.max_parallelism_textfield, "2")
            await entered.wait()
            first = self.form.debounce_tasks["download-max-parallelism"]
            self.preferences.set.assert_not_awaited()
            entered.clear()
            self.type_value(self.form.max_parallelism_textfield, "03")
            await entered.wait()
            second = self.form.debounce_tasks["download-max-parallelism"]
            await asyncio.gather(first, return_exceptions=True)
            self.assertTrue(first.cancelled())
            self.preferences.set.assert_not_awaited()
            release.set()
            await second
        self.preferences.set.assert_awaited_once_with("download-max-parallelism", "3")
        self.assertEqual(self.form.max_parallelism_textfield.value, "3")
        self.assertEqual(self.manager.maximum_concurrency, 3)

    async def test_text_fields_have_independent_timers(self):
        self.form.save_delay = 0.01
        self.type_value(self.form.chunk_size_textfield, "2048")
        self.type_value(self.form.download_timeout_textfield, "120")
        await asyncio.gather(*self.form.debounce_tasks.values())
        self.assertEqual(self.storage["download-chunk-size"], "2048")
        self.assertEqual(self.storage["download-timeout"], "120")

    async def test_reverting_text_before_timeout_cancels_the_write(self):
        self.type_value(self.form.max_parallelism_textfield, "2")
        task = self.form.debounce_tasks["download-max-parallelism"]
        self.type_value(self.form.max_parallelism_textfield, "5")
        await asyncio.gather(task, return_exceptions=True)
        self.assertFalse(self.form.pending_values)
        self.assertFalse(self.form.debounce_tasks)
        self.preferences.set.assert_not_awaited()

    async def test_invalid_numbers_do_not_save_but_do_not_block_other_controls(self):
        for field, minimum, maximum in self.form.numeric_fields:
            original = field.value
            for value in ["", "bad", str(minimum - 1), str(maximum + 1)]:
                self.type_value(field, value)
                await self.form.flush_pending_saves()
                self.assertIsNotNone(field.error)
                self.assertFalse(self.form.busy)
            self.type_value(field, original)
        self.assertTrue(self.form.advanced_fields.visible)
        self.preferences.set.assert_not_awaited()
        self.type_value(self.form.max_parallelism_textfield, "")
        await self.change(self.form.switch_download_photos, False)
        self.preferences.set.assert_awaited_once_with("need-download-photos", "False")
        self.assertIn("download-max-parallelism", self.form.debounce_tasks)

    async def test_invalid_number_is_saved_after_correction(self):
        self.type_value(self.form.max_parallelism_textfield, "")
        await self.form.flush_pending_saves()
        self.assertIsNotNone(self.form.max_parallelism_textfield.error)
        self.type_value(self.form.max_parallelism_textfield, "2")
        self.assertIsNone(self.form.max_parallelism_textfield.error)
        await self.form.flush_pending_saves()
        self.assertEqual(self.storage["download-max-parallelism"], "2")
        self.assertEqual(self.manager.maximum_concurrency, 2)

    async def test_language_saves_and_applies_without_restart(self):
        self.form.on_language_change = AsyncMock()
        await self.change(self.form.language_dropdown, "ru")
        self.assertEqual(self.storage["current-app-language"], "ru")
        self.assertEqual(self.form.localizer.language, "ru")
        self.assertEqual(
            self.form.host_page.locale_configuration.current_locale.language_code,
            "ru",
        )
        self.form.on_language_change.assert_awaited_once_with("ru")

    async def test_failed_language_save_keeps_active_language_and_allows_retry(self):
        self.form.on_language_change = Mock()
        store = self.preferences.set.side_effect

        async def fail_language(key, value):
            if key == "current-app-language":
                return False
            return await store(key, value)

        self.preferences.set.side_effect = fail_language
        await self.change(self.form.language_dropdown, "ru")
        self.assertNotIn("current-app-language", self.storage)
        self.assertEqual(self.form.localizer.language, "en")
        self.assertEqual(self.form.language_dropdown.value, "ru")
        self.form.on_language_change.assert_not_called()
        self.assertTrue(self.form.retry_button.visible)
        # An unrelated successful save must keep the failed language available
        # for retry rather than silently drop its error.
        await self.change(self.form.switch_download_photos, False)
        self.assertTrue(self.form.retry_button.visible)
        self.preferences.set.side_effect = store
        await self.form.flush_pending_saves()
        self.assertEqual(self.form.localizer.language, "ru")
        self.form.on_language_change.assert_called_once_with("ru")
        self.assertFalse(self.form.retry_button.visible)

    async def test_invalid_language_cannot_be_saved(self):
        await self.change(self.form.language_dropdown, "not-supported")
        self.preferences.set.assert_not_awaited()
        self.assertFalse(self.form.busy)

    async def test_storage_failure_rolls_back_the_changed_setting_and_keeps_draft(self):
        store = self.preferences.set.side_effect
        failed = False

        async def fail_once(key, value):
            nonlocal failed
            await store(key, value)
            if key == "current-app-theme" and not failed:
                failed = True
                return False
            return True

        self.preferences.set.side_effect = fail_once
        await self.form.theme_picker.select("dark")
        self.assertEqual(self.storage["current-app-theme"], "light")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.LIGHT)
        self.assertEqual(self.form.theme_picker.value, "dark")
        self.assertTrue(self.form.retry_button.visible)
        self.assertFalse(self.form.busy)
        self.assertIn("Couldn't save", self.form.status_text.value)
        await self.form.flush_pending_saves()
        self.assertEqual(self.storage["current-app-theme"], "dark")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.DARK)
        self.assertFalse(self.form.retry_button.visible)

    async def test_typing_during_persistence_never_cancels_or_overwrites_new_input(
        self,
    ):
        entered, release = asyncio.Event(), asyncio.Event()
        store = self.preferences.set.side_effect

        async def slow_store(key, value):
            if value == "2":
                entered.set()
                await release.wait()
            return await store(key, value)

        self.preferences.set.side_effect = slow_store
        self.form.save_delay = 0
        self.type_value(self.form.max_parallelism_textfield, "2")
        first = self.form.debounce_tasks["download-max-parallelism"]
        await entered.wait()
        self.type_value(self.form.max_parallelism_textfield, "3")
        second = self.form.debounce_tasks["download-max-parallelism"]
        release.set()
        await asyncio.gather(first, second)
        self.assertFalse(first.cancelled())
        self.assertEqual(self.storage["download-max-parallelism"], "3")
        self.assertEqual(self.form.max_parallelism_textfield.value, "3")
        self.assertEqual(self.manager.maximum_concurrency, 3)

    async def test_rapid_toggle_back_is_saved_after_the_in_flight_change(self):
        entered, release = asyncio.Event(), asyncio.Event()
        store = self.preferences.set.side_effect

        async def slow_store(key, value):
            if value == "False":
                entered.set()
                await release.wait()
            return await store(key, value)

        self.preferences.set.side_effect = slow_store
        first = asyncio.create_task(
            self.change(self.form.switch_download_photos, False)
        )
        await entered.wait()
        second = asyncio.create_task(
            self.change(self.form.switch_download_photos, True)
        )
        await asyncio.sleep(0)
        release.set()
        await asyncio.gather(first, second)
        self.assertEqual(self.storage["need-download-photos"], "True")
        self.assertTrue(self.form.switch_download_photos.value)
        self.assertFalse(self.form.pending_values)

    async def test_navigation_flushes_pending_input_before_language_rebuild(self):
        async def rebuild(language):
            self.form.closing = True
            await self.form.flush_pending_saves()
            self.assertEqual(self.storage["download-max-parallelism"], "3")

        self.form.on_language_change = rebuild
        self.type_value(self.form.max_parallelism_textfield, "3")
        task = self.form.debounce_tasks["download-max-parallelism"]
        await self.change(self.form.language_dropdown, "ru")
        self.assertTrue(task.cancelled())
        self.assertEqual(self.storage["current-app-language"], "ru")
        self.assertFalse(self.form.pending_values)

    async def test_unmount_flushes_input_without_refreshing_removed_controls(self):
        self.type_value(self.form.max_parallelism_textfield, "3")
        self.form.will_unmount()
        updates = self.form.update.call_count
        await self.form.flush_pending_saves()
        self.assertEqual(self.storage["download-max-parallelism"], "3")
        self.assertEqual(self.form.update.call_count, updates)

    async def test_load_failure_leaves_form_unavailable(self):
        form = SettingsGroup()
        form.update = Mock()
        with patch(
            "components.settings_group.get_download_settings",
            new=AsyncMock(side_effect=OSError()),
        ):
            await form.set_initial_values()
        self.assertFalse(form.loaded)
        self.assertTrue(form.folder_button.disabled)
        self.assertIn("Couldn't load", form.status_text.value)
        self.preferences.set.assert_not_awaited()

    async def test_leaving_cancels_loading_and_does_not_refresh_removed_controls(self):
        entered = asyncio.Event()

        async def load():
            entered.set()
            await asyncio.Event().wait()

        with patch("components.settings_group.get_download_settings", new=load):
            self.form.load_task = asyncio.create_task(self.form.set_initial_values())
            await entered.wait()
            self.form.will_unmount()
            updates = self.form.update.call_count
            await asyncio.gather(self.form.load_task, return_exceptions=True)
        self.assertTrue(self.form.load_task.cancelled())
        self.assertEqual(self.form.update.call_count, updates)


class DownloadLimitTests(unittest.IsolatedAsyncioTestCase):
    async def test_increase_wakes_existing_waiters_and_decrease_preserves_active_jobs(
        self,
    ):
        manager = DownloadManager(1)
        limiter = manager._semaphore
        await limiter.__aenter__()
        acquired = asyncio.Event()
        release = asyncio.Event()

        async def queued():
            async with limiter:
                acquired.set()
                await release.wait()

        queued_task = asyncio.create_task(queued())
        await asyncio.sleep(0)
        self.assertFalse(acquired.is_set())
        await manager.set_maximum_concurrency(2)
        await asyncio.wait_for(acquired.wait(), 1)
        self.assertIs(manager._semaphore, limiter)
        self.assertEqual(limiter.active, 2)
        await manager.set_maximum_concurrency(1)
        third = asyncio.create_task(limiter.__aenter__())
        await asyncio.sleep(0)
        self.assertFalse(third.done())
        await limiter.__aexit__()
        await asyncio.sleep(0)
        self.assertFalse(third.done())
        release.set()
        await queued_task
        await asyncio.wait_for(third, 1)
        self.assertEqual(limiter.active, 1)
        await limiter.__aexit__()
        self.assertEqual(limiter.active, 0)

    async def test_cancellation_does_not_leak_download_slots(self):
        limiter = DownloadLimiter(1)
        entered = asyncio.Event()

        async def running():
            async with limiter:
                entered.set()
                await asyncio.Event().wait()

        task = asyncio.create_task(running())
        await entered.wait()
        waiter = asyncio.create_task(limiter.__aenter__())
        await asyncio.sleep(0)
        waiter.cancel()
        await asyncio.gather(waiter, return_exceptions=True)
        self.assertEqual(limiter.active, 1)
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        self.assertEqual(limiter.active, 0)
        async with limiter:
            self.assertEqual(limiter.active, 1)
