import asyncio

import flet as ft

import __version__ as app_version
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_default_downloads_folder
from pages.auth_management import AuthManagementPage
from pages.download_image_by_link import DownloadImageByLinkPage
from pages.download_post import DownloadPostPage
from pages.download_several_posts import DownloadSeveralPostsPage
from pages.downloads_center import DownloadsCenterPage
from pages.merge_author_content import MergeAuthorContentPage
from pages.settings_page import SettingsPage
from pages.welcome_page import WelcomePage
from themes import LIGHT_THEME, DARK_THEME


async def main(page: ft.Page):
    page.title = f"{app_version.NAME} {app_version.VERSION}"
    page.theme = LIGHT_THEME
    page.dark_theme = DARK_THEME
    page.theme_mode = await ft.SharedPreferences().get("current-app-theme") or "system"

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
            case "/auth-management":
                page.views.append(AuthManagementPage(manager))
            case "/merge-author-content":
                page.views.append(MergeAuthorContentPage(manager))
            case "/download-several-posts":
                page.views.append(DownloadSeveralPostsPage(manager))
            case "/download-media-by-link":
                page.views.append(DownloadImageByLinkPage(manager))

        page.update()

    page.on_route_change = route_change
    route_change(page)

    logger.info("Router is set up, starting task manager...")

    async def check_active_downloads_on_close():
        if await manager.get_active_tasks_count() > 0:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Some downloads are incomplete"),
                    content=ft.Text("Are you sure you want to exit the app?"),
                    actions=[
                        ft.TextButton("No", on_click=lambda e: page.pop_dialog()),
                        ft.TextButton("Yes", on_click=lambda e: asyncio.create_task(page.window.destroy()))
                    ],
                    open=True,
                )
            )
            page.update()
        else:
            await page.window.destroy()

    def window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.CLOSE:
            asyncio.create_task(check_active_downloads_on_close())
    page.window.prevent_close = True
    page.window.on_event = window_event

    asyncio.create_task(manager.mainloop())
    logger.info("Task manager started")


if __name__ == "__main__":
    logger = setup_logger()
    logger.info(f"Starting {app_version.NAME} v{app_version.VERSION}...")
    try:
        ft.run(main)
    except Exception as err:
        logger.critical("Unhandled exception", exc_info=err)
