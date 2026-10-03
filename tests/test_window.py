import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import flet as ft
from screeninfo import Monitor

from src.core.window import configure_window, startup_window_size


class WindowTests(unittest.TestCase):
    def test_window_fits_display_at_different_system_scales(self):
        cases = [
            ("darwin", 1440, 932, 2),  # Retina reports logical points.
            ("win32", 2880, 1864, 2),
            ("linux", 1920, 1080, 1.5),
            ("linux", 1024, 768, 1),
            ("win32", 3840, 2160, 1),
            ("linux", 1920, 600, 1),
        ]
        for platform, width, height, ratio in cases:
            with self.subTest(platform=platform, width=width, ratio=ratio):
                with (
                    patch("src.core.window.sys.platform", platform),
                    patch(
                        "src.core.window.get_monitors",
                        return_value=[Monitor(0, 0, width, height, is_primary=True)],
                    ),
                ):
                    window_width, window_height = startup_window_size(ratio)
                logical_ratio = 1 if platform == "darwin" else ratio
                self.assertLessEqual(window_width, width / logical_ratio * 0.7)
                self.assertLessEqual(window_height, height / logical_ratio * 0.8)
                self.assertLessEqual(window_width, 1200)
                self.assertLessEqual(window_height, 750)

    def test_primary_display_is_used(self):
        with patch(
            "src.core.window.get_monitors",
            return_value=[
                Monitor(1440, 0, 3840, 2160),
                Monitor(0, 0, 1000, 800, is_primary=True),
            ],
        ):
            self.assertEqual(startup_window_size(1), (700, 437))

    def test_compact_window_is_centered_and_shown_if_detection_fails(self):
        page = SimpleNamespace(
            web=False,
            platform=ft.PagePlatform.MACOS,
            media=SimpleNamespace(device_pixel_ratio=2),
            window=SimpleNamespace(center=AsyncMock()),
            update=Mock(),
        )
        with (
            patch("src.core.window.get_monitors", side_effect=RuntimeError),
            self.assertLogs("src.core.window", level="WARNING"),
        ):
            asyncio.run(configure_window(page))
        self.assertEqual((page.window.width, page.window.height), (900, 560))
        page.window.center.assert_awaited_once()
        self.assertTrue(page.window.visible)

    def test_minimum_size_does_not_override_small_display_limit(self):
        page = SimpleNamespace(
            web=False,
            platform=ft.PagePlatform.MACOS,
            media=SimpleNamespace(device_pixel_ratio=2),
            window=SimpleNamespace(center=AsyncMock()),
            update=Mock(),
        )
        with patch("src.core.window.startup_window_size", return_value=(560, 350)):
            asyncio.run(configure_window(page))
        self.assertEqual(page.window.min_width, 560)
        self.assertEqual(page.window.min_height, 350)
        page.window.center.assert_awaited_once()
        self.assertTrue(page.window.visible)

    def test_web_and_mobile_skip_native_display_detection(self):
        for web, platform in [
            (True, ft.PagePlatform.MACOS),
            (False, ft.PagePlatform.IOS),
        ]:
            with patch("src.core.window.get_monitors") as get_monitors:
                asyncio.run(
                    configure_window(SimpleNamespace(web=web, platform=platform))
                )
                get_monitors.assert_not_called()
