import flet as ft

import __version__ as app_version
import components
from components.soft_layout import page_shell
from core.downloads_manager import DownloadManager


class SettingsPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/settings"
        self.padding = self.spacing = 0
        self.settings_group = components.SettingsGroup(manager, self.preview_theme)
        self.shell = page_shell(
            components.AppBar(manager),
            ft.Column(
                spacing=24,
                controls=[
                    ft.Text("Settings", size=24, weight=ft.FontWeight.W_500),
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
            self.go_to_index,
            self.go_to_feedback,
            width=744,
        )
        self.controls = [self.shell]

    def preview_theme(self, value):
        page = self.settings_group.host_page
        if page:
            page.theme_mode = ft.ThemeMode(value)
            page.update()

    async def go_to_index(self, e=None):
        await self.page.push_route("/")

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")
