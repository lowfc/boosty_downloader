import asyncio

import flet as ft

import __version__ as app_version
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from pages.download_post import DownloadPostPage
from pages.downloads_center import DownloadsCenterPage
from pages.settings_page import SettingsPage
from pages.welcome_page import WelcomePage
from themes import LIGHT_THEME, DARK_THEME


async def main(page: ft.Page):
    page.title = f"{app_version.NAME} {app_version.VERSION}"
    page.theme = LIGHT_THEME
    page.dark_theme = DARK_THEME
    page.theme_mode = await ft.SharedPreferences().get("current-app-theme")
    logger = setup_logger()
    logger.info(f"Starting {app_version.NAME} v{app_version.VERSION}...")

    manager = DownloadManager()

    def route_change(e):
        page.views.clear()

        match page.route:
            case "/":
                page.views.append(WelcomePage(manager))
            case "/settings":
                page.views.append(SettingsPage(manager))
            case "/download-post":
                page.views.append(DownloadPostPage(manager))
            case "/downloads-center":
                page.views.append(DownloadsCenterPage(manager))

        page.update()

    page.on_route_change = route_change
    await page.push_route("/download-post")
    route_change(page)

    logger.info("Router is set up, starting task manager...")

    # def window_event(e: ft.WindowEvent):
    #     if e.type == ft.WindowEventType.CLOSE:
    #         asyncio.create_task(page.window.destroy())
    # page.window.prevent_close = True
    # page.window.on_event = window_event

    asyncio.create_task(manager.mainloop())
    logger.info("Task manager started")

ft.run(main)
