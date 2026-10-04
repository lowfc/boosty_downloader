import flet as ft

import __version__ as app_version
import components
from components.soft_layout import page_shell
from core.downloads_manager import DownloadManager
from localization import Localizer


class SettingsPage(ft.View):
    def __init__(
        self, manager: DownloadManager, localizer=None, on_language_change=None
    ):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.route = "/settings"
        self.padding = self.spacing = 0
        self.settings_group = components.SettingsGroup(
            manager,
            self.preview_theme,
            localizer=self.localizer,
            on_language_change=on_language_change,
        )
        self.shell = page_shell(
            components.AppBar(manager, localizer=self.localizer),
            ft.Column(
                spacing=24,
                controls=[
                    ft.Text(self.tr("Settings"), size=24, weight=ft.FontWeight.W_500),
                    self.settings_group,
                ],
            ),
            ft.Text(
                f"{app_version.NAME} · {app_version.VERSION}",
                size=11,
                expand=True,
                color=ft.Colors.ON_SURFACE_VARIANT,
            ),
            ft.Icons.INFO_OUTLINE,
            self.go_to_feedback,
            width=744,
            localizer=self.localizer,
        )
        self.controls = [self.shell]

    def preview_theme(self, value):
        page = self.settings_group.host_page
        if page:
            page.theme_mode = ft.ThemeMode(value)
            page.update()

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")
