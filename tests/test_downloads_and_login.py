import asyncio
import base64
import datetime
import json
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import flet as ft

from components.task_item import TaskItem
from core.defs.tasks import TaskError, TaskInfo
from core.downloads_manager import DownloadManager
from core.task import Task
from pages.auth_management import AuthManagementPage
from pages.downloads_center import DownloadsCenterPage


def login_token(expires):
    return base64.b64encode(
        json.dumps(
            {
                "authorization": "test-only",
                "full_cookie": "test-only",
                "expires_in": expires * 1000,
            }
        ).encode()
    ).decode()


class DownloadsTests(unittest.IsolatedAsyncioTestCase):
    async def test_queue_cancel_all_preserves_completed_tasks_and_can_retry(self):
        manager = DownloadManager()
        await manager.add_task("test-author", "queued")
        await manager.add_task("test-author", "running")
        await manager.add_task("test-author", "complete")
        manager._tasks["running"]._pending = True
        manager._tasks["running"]._running = True
        manager._tasks["complete"]._finished = True
        manager._tasks["complete"]._done = True
        page = DownloadsCenterPage(manager)
        page.update = Mock()
        await page.refresh_tasks()
        self.assertEqual(page.summary.value, "1 downloading · 1 queued")
        self.assertEqual(
            [slot.status.value for slot in page.slots[:3]], ["Complete", "0%", "Queued"]
        )
        await page.on_all_tasks_cancel()
        await page.refresh_tasks()
        self.assertFalse(page.stop_all_button.visible)
        self.assertIsNone(manager._tasks["complete"].error_description)
        self.assertEqual(
            manager._tasks["queued"].error_description, TaskError.CANCELLED
        )
        with patch.object(Task, "launch") as launch:
            await page.slots[2].on_retry()
            launch.assert_called_once()
        self.assertFalse(manager._tasks["queued"].finished)
        self.assertIsNone(manager._tasks["queued"].error_description)

    async def test_waiting_for_semaphore_is_queued_and_stop_removes_it(self):
        task = Task(asyncio.Semaphore(0), "test-author", "queued")
        task.launch()
        await asyncio.sleep(0)
        self.assertTrue(task.pending)
        self.assertFalse(task.running)
        runner = task._task
        await task.stop()
        await asyncio.gather(runner, return_exceptions=True)
        self.assertTrue(task.finished)
        self.assertFalse(task.running)
        self.assertEqual(task.error_description, TaskError.CANCELLED)

    async def test_task_slot_reuses_progress_and_retry_without_stale_actions(self):
        cancel, retry = AsyncMock(), AsyncMock()
        info = TaskInfo(
            0.62,
            "Test post",
            "test-author",
            "id",
            None,
            False,
            3,
            1024**2,
            running=True,
        )
        item = TaskItem(info, visible=True, on_cancel=cancel, on_retry=retry)
        self.assertEqual(item.status.value, "62%")
        await item.on_cancel()
        cancel.assert_awaited_once_with(info)
        info.finished, info.error = True, TaskError.ACCESS_DENIED
        item.update_view(info, True)
        self.assertEqual(item.status.value, "Failed")
        self.assertFalse(item.progress_bar.visible)
        await item.on_retry()
        retry.assert_awaited_once_with(info)
        info.finished, info.error, info.running = False, None, False
        item.update_view(info, True)
        self.assertEqual(item.status.value, "Queued")
        self.assertEqual(item.icon.content.icon, ft.Icons.SCHEDULE)
        self.assertIs(item.trailing_button.content, item.stop_button)
        info.finished = True
        item.update_view(info, True)
        self.assertEqual(item.status.value, "Complete")
        self.assertEqual(item.icon.content.icon, ft.Icons.CHECK)
        self.assertTrue(item.folder_open_button.disabled)


class LoginTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.page = AuthManagementPage(DownloadManager())
        self.page.update = Mock()
        self.page.toolbar.on_auth_change = None

    async def test_empty_invalid_and_expired_tokens_are_not_saved(self):
        now = datetime.datetime.now(datetime.UTC).timestamp()
        with patch(
            "pages.auth_management.AuthorizationProvider.authorize",
            new_callable=AsyncMock,
        ) as save:
            for value, expected in [
                ("", "Paste your Boosty token"),
                ("not-a-token", "isn't valid"),
                (login_token(now - 60), "expired"),
            ]:
                self.page.token_text_field.value = value
                await self.page.save_new_token()
                self.assertTrue(self.page.token_error.visible)
                self.assertIn(expected, self.page.token_error.value)
            save.assert_not_awaited()

    async def test_login_logout_and_expiry_restore_correct_view(self):
        future = datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=7)
        self.page.token_text_field.value = login_token(future.timestamp())
        with (
            patch(
                "pages.auth_management.AuthorizationProvider.authorize",
                new_callable=AsyncMock,
            ) as save,
            patch(
                "pages.auth_management.AuthorizationProvider.get_token_valid_to",
                new=AsyncMock(
                    side_effect=[
                        future,
                        None,
                        future,
                        future - datetime.timedelta(days=8),
                    ]
                ),
            ),
            patch("pages.auth_management.ft.SharedPreferences") as preferences,
        ):
            preferences.return_value.remove = AsyncMock()
            await self.page.save_new_token()
            save.assert_awaited_once()
            self.assertEqual(self.page.title.value, "Account")
            self.assertTrue(self.page.deauth_view.visible)
            self.assertEqual(self.page.toolbar.status_text.value, "Logged in")
            self.assertEqual(self.page.token_text_field.value, "")
            await self.page.logout()
            self.assertEqual(preferences.return_value.remove.await_count, 3)
            self.assertTrue(self.page.auth_view.visible)
            await self.page.render_page()
            self.assertTrue(self.page.deauth_view.visible)
            await self.page.render_page()
            self.assertTrue(self.page.auth_view.visible)
            self.assertEqual(self.page.toolbar.login_button.content, "Log in")

    async def test_copy_script_resolves_from_source_and_paste_clears_error(self):
        with patch("pages.auth_management.ft.Clipboard") as clipboard:
            clipboard.return_value.set = AsyncMock()
            clipboard.return_value.get = AsyncMock(return_value=" test-token ")
            await self.page.copy_script()
            script = (
                Path(__file__).resolve().parents[1] / "src/js/auth_getter_minify.js"
            )
            clipboard.return_value.set.assert_awaited_once_with(script.read_text())
            self.assertEqual(self.page.copy_script_button.content, "Copied")
            self.page.token_error.visible = True
            await self.page.paste_token()
            self.assertEqual(self.page.token_text_field.value, "test-token")
            self.assertFalse(self.page.token_error.visible)
            self.page.will_unmount()
            await asyncio.gather(self.page.copy_task, return_exceptions=True)
