import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import flet as ft

import __version__ as app_version
from core.downloads_manager import DownloadManager
from pages.feedback_and_bugs import FeedbackAndBugsPage


class FeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.log_path = Path(self.temp.name) / "runtime.log"
        self.view = FeedbackAndBugsPage(DownloadManager())
        self.view.update = Mock()
        self.addCleanup(self.view.will_unmount)
        for patcher in (
            patch("pages.feedback_and_bugs.Path", return_value=self.log_path),
            patch("pages.feedback_and_bugs.logger"),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    async def load(self):
        with patch.object(
            self.view, "get_device_info", new=AsyncMock(return_value="macOS · arm64")
        ):
            await self.view.get_app_info()

    async def test_full_diagnostics_are_copied_even_when_details_are_collapsed(self):
        self.log_path.write_text(
            "[INFO] Started\n[ERROR] Download failed\n", encoding="utf-8"
        )
        self.assertTrue(self.view.copy_button.disabled)
        await self.load()
        self.assertFalse(self.view.logs_field.visible)
        self.assertEqual(self.view.device_text.value, "macOS · arm64")
        expected = (
            f"App version: v{app_version.VERSION} (build {app_version.BUILD})\n"
            "macOS · arm64\n\nLast run log:\n[INFO] Started\n[ERROR] Download failed\n"
        )
        with patch("pages.feedback_and_bugs.ft.Clipboard") as clipboard:
            clipboard.return_value.set = AsyncMock()
            await self.view.copy_log()
        clipboard.return_value.set.assert_awaited_once_with(expected)
        self.assertEqual(self.view.copy_button.content, "Copied")
        self.assertFalse(self.view.copy_button.disabled)
        self.view.copy_task.cancel()
        await asyncio.gather(self.view.copy_task, return_exceptions=True)
        with patch("pages.feedback_and_bugs.asyncio.sleep", new=AsyncMock()):
            await self.view.reset_copy_button()
        self.assertEqual(self.view.copy_button.content, "Copy diagnostics")

    async def test_missing_or_unreadable_log_keeps_version_and_copy_available(self):
        await self.load()
        self.assertIn("No run log available.", self.view.log_text.value)
        self.assertFalse(self.view.copy_button.disabled)
        with patch(
            "pages.feedback_and_bugs.aiofiles.open", side_effect=PermissionError
        ):
            await self.load()
        self.assertIn("Run log unavailable.", self.view.log_text.value)
        self.assertIn(f"v{app_version.VERSION}", self.view.log_text.value)
        self.assertFalse(self.view.copy_button.disabled)

    async def test_clipboard_failure_allows_retry_without_showing_false_success(self):
        await self.load()
        with patch("pages.feedback_and_bugs.ft.Clipboard") as clipboard:
            clipboard.return_value.set = AsyncMock(
                side_effect=RuntimeError("unavailable")
            )
            await self.view.copy_log()
            self.assertTrue(self.view.copy_error.visible)
            self.assertEqual(self.view.copy_button.content, "Copy diagnostics")
            self.assertFalse(self.view.copy_button.disabled)
            clipboard.return_value.set.side_effect = None
            await self.view.copy_log()
            self.assertFalse(self.view.copy_error.visible)
            self.assertEqual(self.view.copy_button.content, "Copied")

    async def test_copy_while_loading_does_not_write_an_empty_clipboard(self):
        with patch("pages.feedback_and_bugs.ft.Clipboard") as clipboard:
            await self.view.copy_log()
        clipboard.assert_not_called()

    async def test_leaving_cancels_loading_and_delayed_copy_feedback(self):
        entered = asyncio.Event()

        async def device_info():
            entered.set()
            await asyncio.Event().wait()

        with patch.object(self.view, "get_device_info", new=device_info):
            self.view.did_mount()
            await entered.wait()
            self.view.copy_task = asyncio.create_task(self.view.reset_copy_button())
            self.view.will_unmount()
            updates = self.view.update.call_count
            await asyncio.gather(
                self.view.load_task, self.view.copy_task, return_exceptions=True
            )
        self.assertTrue(self.view.load_task.cancelled())
        self.assertTrue(self.view.copy_task.cancelled())
        self.assertEqual(self.view.update.call_count, updates)

    async def test_leaving_during_copy_does_not_update_removed_controls(self):
        await self.load()
        entered, release = asyncio.Event(), asyncio.Event()

        async def copy(value):
            entered.set()
            await release.wait()

        with patch("pages.feedback_and_bugs.ft.Clipboard") as clipboard:
            clipboard.return_value.set = copy
            task = asyncio.create_task(self.view.copy_log())
            await entered.wait()
            self.view.will_unmount()
            updates = self.view.update.call_count
            release.set()
            await task
        self.assertIsNone(self.view.copy_task)
        self.assertEqual(self.view.update.call_count, updates)

    async def test_device_info_for_supported_platforms_and_service_failure(self):
        mac = Mock(spec=ft.MacOsDeviceInfo)
        mac.major_version, mac.minor_version, mac.patch_version, mac.arch = (
            15,
            1,
            2,
            "arm64",
        )
        windows = Mock(spec=ft.WindowsDeviceInfo)
        windows.product_name, windows.edition_id = "Windows 11", "Professional"
        linux = Mock(spec=ft.LinuxDeviceInfo)
        linux.pretty_name = "Ubuntu 24.04 LTS"
        host = SimpleNamespace(get_device_info=AsyncMock())
        with patch.object(
            FeedbackAndBugsPage, "page", new_callable=PropertyMock, return_value=host
        ):
            for info, expected in (
                (mac, "macOS 15.1.2 · arm64"),
                (windows, "Windows 11 Professional"),
                (linux, "Ubuntu 24.04 LTS"),
                (object(), "Unknown device"),
            ):
                host.get_device_info.return_value = info
                self.assertEqual(await self.view.get_device_info(), expected)
            host.get_device_info.side_effect = RuntimeError("unavailable")
            self.assertEqual(
                await self.view.get_device_info(), "Device information unavailable"
            )

    async def test_repeated_copy_replaces_pending_reset(self):
        await self.load()
        with patch("pages.feedback_and_bugs.ft.Clipboard") as clipboard:
            clipboard.return_value.set = AsyncMock()
            await self.view.copy_log()
            first_reset = self.view.copy_task
            await self.view.copy_log()
            await asyncio.gather(first_reset, return_exceptions=True)
        self.assertTrue(first_reset.cancelled())
        self.assertIsNot(self.view.copy_task, first_reset)
        self.assertEqual(self.view.copy_button.content, "Copied")
