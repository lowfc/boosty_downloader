import asyncio
import logging
import sys

import flet as ft
from screeninfo import get_monitors

logger = logging.getLogger(__name__)

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 750


def startup_window_size(pixel_ratio: float) -> tuple[int, int]:
    """Fit the window to the primary display, in Flet's logical pixels."""
    monitors = get_monitors()
    monitor = next((item for item in monitors if item.is_primary), monitors[0])
    # AppKit already reports logical points, including on Retina displays.
    # Windows and Linux report physical pixels instead.
    ratio = 1 if sys.platform == "darwin" else pixel_ratio or 1
    screen_width = monitor.width / ratio
    screen_height = monitor.height / ratio
    if screen_width <= 0 or screen_height <= 0:
        raise ValueError("Invalid display dimensions")
    width = min(DEFAULT_WIDTH, int(screen_width * 0.7))
    height = min(int(width * DEFAULT_HEIGHT / DEFAULT_WIDTH), int(screen_height * 0.8))
    return width, height


async def configure_window(page: ft.Page):
    """Set desktop startup dimensions without changing web or mobile views."""
    if page.web or page.platform not in (
        ft.PagePlatform.MACOS,
        ft.PagePlatform.WINDOWS,
        ft.PagePlatform.LINUX,
    ):
        return

    try:
        width, height = await asyncio.to_thread(
            startup_window_size, page.media.device_pixel_ratio
        )
    except Exception:
        logger.warning(
            "Cannot detect display size; using a compact window", exc_info=True
        )
        width, height = 900, 560

    page.window.width = width
    page.window.height = height
    page.window.min_width = min(800, width)
    page.window.min_height = min(400, height)
    page.update()
    await page.window.center()
    page.window.visible = True
    page.update()
