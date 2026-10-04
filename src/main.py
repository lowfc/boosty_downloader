import asyncio

import flet as ft

import __version__ as app_version
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_download_settings
from core.window import configure_window
from localization import initialize_localization
from pages.auth_management import AuthManagementPage
from pages.download_image_by_link import DownloadImageByLinkPage
from pages.download_post import DownloadPostPage
from pages.download_several_posts import DownloadSeveralPostsPage
from pages.downloads_center import DownloadsCenterPage
from pages.feedback_and_bugs import FeedbackAndBugsPage
from pages.merge_author_content import MergeAuthorContentPage
from pages.settings_page import SettingsPage
from pages.welcome_page import WelcomePage
from themes import DARK_THEME, LIGHT_THEME

logger = setup_logger()


async def main(page: ft.Page):
    page.title = f"{app_version.NAME} {app_version.VERSION}"
    page.theme = LIGHT_THEME
    page.dark_theme = DARK_THEME
    page.fonts = {"LanguageFlags": "fonts/language-flags.ttf"}
    page.theme_mode = await ft.SharedPreferences().get("current-app-theme") or "system"
    localizer = await initialize_localization(page)
    tr = localizer.t

    try:
        settings = await get_download_settings()
    except (TypeError, ValueError):
        logger.warning("Invalid saved download settings; using the default concurrency")
        settings = None
    manager = DownloadManager(settings.max_parallelism if settings else 5)

    route_lock = asyncio.Lock()

    async def route_change(e):
        async with route_lock:
            for view in page.views:
                if isinstance(view, SettingsPage):
                    view.settings_group.closing = True
                    view.settings_group.set_editing_enabled(False)
                    await view.settings_group.flush_pending_saves()
            page.views.clear()

            match page.route:
                case "/":
                    page.views.append(WelcomePage(manager, localizer=localizer))
                case "/settings":
                    page.views.append(
                        SettingsPage(
                            manager,
                            localizer=localizer,
                            on_language_change=language_change,
                        )
                    )
                case "/download-post":
                    page.views.append(DownloadPostPage(manager, localizer=localizer))
                case "/downloads-center":
                    page.views.append(DownloadsCenterPage(manager, localizer=localizer))
                case "/auth-management":
                    page.views.append(AuthManagementPage(manager, localizer=localizer))
                case "/merge-author-content":
                    page.views.append(
                        MergeAuthorContentPage(manager, localizer=localizer)
                    )
                case "/download-several-posts":
                    page.views.append(
                        DownloadSeveralPostsPage(manager, localizer=localizer)
                    )
                case "/download-media-by-link":
                    page.views.append(
                        DownloadImageByLinkPage(manager, localizer=localizer)
                    )
                case "/feedback-and-bugs":
                    page.views.append(FeedbackAndBugsPage(manager, localizer=localizer))

            page.update()

    async def language_change(language):
        localizer.set_language(language)
        localizer.configure_page(page)
        await route_change(None)

    page.on_route_change = route_change
    await route_change(page)

    logger.info("Router is set up, starting task manager...")

    async def close_window(e=None):
        for view in page.views:
            if isinstance(view, SettingsPage):
                view.settings_group.closing = True
                await view.settings_group.flush_pending_saves()
        await page.window.destroy()

    async def check_active_downloads_on_close():
        if await manager.get_active_tasks_count() > 0:
            page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text(tr("Some downloads are incomplete")),
                    content=ft.Text(tr("Are you sure you want to exit the app?")),
                    actions=[
                        ft.TextButton(tr("No"), on_click=lambda e: page.pop_dialog()),
                        ft.TextButton(
                            tr("Yes"),
                            on_click=close_window,
                        ),
                    ],
                    open=True,
                )
            )
            page.update()
        else:
            await close_window()

    def window_event(e: ft.WindowEvent):
        if e.type == ft.WindowEventType.CLOSE:
            asyncio.create_task(check_active_downloads_on_close())

    page.window.prevent_close = True
    page.window.on_event = window_event

    await configure_window(page)

    asyncio.create_task(manager.mainloop())
    logger.info("Task manager started")


if __name__ == "__main__":
    logger.info(f"Starting {app_version.NAME} v{app_version.VERSION}...")
    try:
        ft.run(main, view=ft.AppView.FLET_APP_HIDDEN)
    except Exception as err:
        logger.critical("Unhandled exception", exc_info=err)
