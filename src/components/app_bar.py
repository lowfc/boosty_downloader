import asyncio
import datetime
from collections.abc import Callable

import flet as ft

from core.authorization_provider import AuthorizationProvider
from core.downloads_manager import DownloadManager


@ft.control
class AppBar(ft.Container):
    def __init__(
        self,
        manager: DownloadManager,
        on_auth_change: Callable[[bool], None] | None = None,
    ):
        super().__init__()
        self.manager = manager
        self.on_auth_change = on_auth_change
        self.upd_task = None
        self.logged_in = None
        navigation_button_style = ft.ButtonStyle(
            color=ft.Colors.ON_SURFACE,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
            side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT),
            shape=ft.RoundedRectangleBorder(radius=8),
            padding=ft.Padding.symmetric(horizontal=14, vertical=8),
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
        )
        self.home_button = ft.OutlinedButton(
            "Home",
            icon=ft.Icon(ft.Icons.HOME_OUTLINED, size=16),
            height=32,
            on_click=self.go_to_home,
            style=navigation_button_style,
        )
        self.status_icon = ft.Icon(
            ft.Icons.CIRCLE, size=6, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self.status_text = ft.Text(
            "Not logged in", size=13, color=ft.Colors.ON_SURFACE_VARIANT
        )
        self.login_button = ft.OutlinedButton(
            "Log in",
            height=32,
            on_click=self.go_to_auth_management,
            style=navigation_button_style,
        )
        self.downloads_button = ft.TextButton(
            "Downloads",
            icon=ft.Icons.DOWNLOAD_OUTLINED,
            on_click=self.go_to_downloads_center,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_SURFACE_VARIANT, text_style=ft.TextStyle(size=13)
            ),
        )
        self.bgcolor = ft.Colors.SURFACE
        self.padding = ft.Padding.symmetric(horizontal=24, vertical=12)
        self.border = ft.Border.only(bottom=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT))
        self.content = ft.ResponsiveRow(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            run_spacing=0,
            controls=[
                ft.Row(
                    col={"xs": 12, "sm": 8, "md": 7, "lg": 6},
                    spacing=12,
                    controls=[
                        self.home_button,
                        ft.Container(
                            width=1, height=24, bgcolor=ft.Colors.OUTLINE_VARIANT
                        ),
                        ft.Row(
                            controls=[self.status_icon, self.status_text], spacing=8
                        ),
                        self.login_button,
                    ],
                ),
                ft.Row(
                    col={"xs": 12, "sm": 4, "md": 5, "lg": 6},
                    alignment=ft.MainAxisAlignment.END,
                    spacing=6,
                    controls=[
                        self.downloads_button,
                        ft.IconButton(
                            ft.Icons.TUNE,
                            icon_size=19,
                            icon_color=ft.Colors.ON_SURFACE_VARIANT,
                            tooltip="Settings",
                            on_click=self.go_to_settings,
                        ),
                    ],
                ),
            ],
        )

    def did_mount(self):
        self.upd_task = asyncio.create_task(self.update_task())

    def will_unmount(self):
        if self.upd_task:
            self.upd_task.cancel()

    def set_auth_status(self, logged_in: bool):
        self.status_text.value = "Logged in" if logged_in else "Not logged in"
        self.status_icon.icon = (
            ft.Icons.CHECK_CIRCLE_OUTLINE if logged_in else ft.Icons.CIRCLE
        )
        self.status_icon.size = 15 if logged_in else 6
        self.status_icon.color = (
            ft.Colors.PRIMARY if logged_in else ft.Colors.ON_SURFACE_VARIANT
        )
        self.login_button.content = "Account" if logged_in else "Log in"
        if self.logged_in != logged_in:
            self.logged_in = logged_in
            if self.on_auth_change:
                self.on_auth_change(logged_in)

    async def update_task(self):
        while True:
            expires_at = await AuthorizationProvider.get_token_valid_to()
            self.set_auth_status(
                bool(expires_at and datetime.datetime.now(datetime.UTC) < expires_at)
            )
            count = self.manager.total_tasks
            self.downloads_button.badge = (
                ft.Badge(label=str(count), bgcolor=ft.Colors.PRIMARY) if count else None
            )
            self.update()
            await asyncio.sleep(1)

    async def go_to_home(self, e=None):
        if self.page.route != "/":
            await self.page.push_route("/")

    async def go_to_settings(self, e=None):
        await self.page.push_route("/settings")

    async def go_to_auth_management(self, e=None):
        await self.page.push_route("/auth-management")

    async def go_to_downloads_center(self, e=None):
        await self.page.push_route("/downloads-center")
