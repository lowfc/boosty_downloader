import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import flet as ft

from components.settings_group import SettingsGroup
from core.download_limiter import DownloadLimiter
from core.downloads_manager import DownloadManager
from pages.settings_page import SettingsPage


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
        self.preview = Mock()
        self.form = SettingsGroup(self.manager, self.preview)
        self.form.update = Mock()
        self.form.host_page = SimpleNamespace(
            theme_mode=ft.ThemeMode.LIGHT, update=Mock(), schedule_update=Mock()
        )
        await self.form.set_initial_values()

    async def test_loaded_values_and_drafts_do_not_write_preferences(self):
        self.assertEqual(self.form.folder, "/custom/downloads")
        self.assertEqual(self.form.max_parallelism_textfield.value, "5")
        self.assertEqual(self.form.download_timeout_textfield.value, "3600")
        self.assertEqual(self.form.theme_picker.value, "light")
        self.assertFalse(self.form.switch_download_audios.value)
        self.assertTrue(self.form.save_button.disabled)
        self.form.theme_picker.select("dark")
        self.preview.assert_called_once_with("dark")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.LIGHT)
        self.assertFalse(self.form.save_button.disabled)
        self.form.theme_picker.select("light")
        self.assertTrue(self.form.save_button.disabled)
        self.preferences.set.assert_not_awaited()

    async def test_folder_and_all_settings_commit_together(self):
        with patch("components.settings_group.ft.FilePicker") as picker:
            picker.return_value.get_directory_path = AsyncMock(return_value=None)
            await self.form.pick_download_folder()
            self.assertTrue(self.form.save_button.disabled)
            picker.return_value.get_directory_path.return_value = "/custom/new-folder"
            await self.form.pick_download_folder()
        self.preferences.set.assert_not_awaited()
        self.form.theme_picker.select("dark")
        self.form.max_parallelism_textfield.value = "03"
        self.form.switch_download_videos.value = False
        self.form.mark_changed()
        self.assertTrue(self.form.video_size_dropdown.disabled)
        await self.form.apply_settings()
        self.assertEqual(len(self.storage), 11)
        self.assertEqual(self.storage["download-folder"], "/custom/new-folder")
        self.assertEqual(self.storage["download-max-parallelism"], "3")
        self.assertEqual(self.storage["current-app-theme"], "dark")
        self.assertEqual(self.storage["need-download-videos"], "False")
        self.assertEqual(self.storage["preferred-video-size"], "full_hd")
        self.assertEqual(self.manager.maximum_concurrency, 3)
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.DARK)
        self.assertEqual(self.form.status_text.value, "Changes saved.")
        self.assertFalse(self.form.max_parallelism_textfield.read_only)
        self.assertTrue(self.form.save_button.disabled)

    async def test_invalid_numbers_never_write_and_reveal_advanced_errors(self):
        for field, minimum, maximum in self.form.numeric_fields:
            original = field.value
            for value in ["", "bad", str(minimum - 1), str(maximum + 1)]:
                field.value = value
                self.form.mark_changed()
                await self.form.apply_settings()
                self.assertIsNotNone(field.error)
                self.assertFalse(self.form.busy)
            field.value = str(minimum)
            self.assertTrue(self.form.validate())
            field.value = str(maximum)
            self.assertTrue(self.form.validate())
            field.value = original
        self.assertTrue(self.form.advanced_fields.visible)
        self.preferences.set.assert_not_awaited()

    async def test_storage_failure_restores_old_settings_and_keeps_draft(self):
        old = dict(self.storage)
        original_store = self.preferences.set.side_effect
        failed = False

        async def fail_once(key, value):
            nonlocal failed
            if key == "need-download-videos" and not failed:
                failed = True
                return False
            return await original_store(key, value)

        self.preferences.set.side_effect = fail_once
        self.form.theme_picker.select("dark")
        self.form.max_parallelism_textfield.value = "2"
        await self.form.apply_settings()
        self.assertEqual(self.storage, old)
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.LIGHT)
        self.assertEqual(self.manager.maximum_concurrency, 5)
        self.assertEqual(self.form.theme_picker.value, "dark")
        self.assertFalse(self.form.save_button.disabled)
        self.assertFalse(self.form.busy)
        self.assertIn("Couldn't save", self.form.status_text.value)
        await self.form.apply_settings()
        self.assertEqual(self.manager.maximum_concurrency, 2)
        self.assertTrue(self.form.save_button.disabled)

    async def test_load_failure_leaves_form_unavailable(self):
        form = SettingsGroup()
        form.update = Mock()
        with patch(
            "components.settings_group.get_download_settings",
            new=AsyncMock(side_effect=OSError()),
        ):
            await form.set_initial_values()
        self.assertFalse(form.loaded)
        self.assertTrue(form.save_button.disabled)
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

    def test_theme_preview_is_restored_when_leaving_without_saving(self):
        view = SettingsPage(self.manager)
        view.settings_group.host_page = self.form.host_page
        view.settings_group.saved_values = self.form.saved_values
        self.form.host_page.schedule_update = Mock()
        view.preview_theme("dark")
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.DARK)
        self.form.host_page.update.assert_called_once()
        view.settings_group.discard_theme_preview()
        self.assertEqual(self.form.host_page.theme_mode, ft.ThemeMode.LIGHT)
        self.preferences.set.assert_not_awaited()


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
