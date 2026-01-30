import asyncio
import datetime

import flet as ft

from core.authorization_provider import AuthorizationProvider
from core.downloads_manager import DownloadManager


@ft.control
class AppBar(ft.AppBar):

    async def go_to_settings(self):
        await self.page.push_route("/settings")

    async def go_to_auth_management(self):
        await self.page.push_route("/auth-management")

    async def go_to_downloads_center(self):
        await self.page.push_route("/downloads-center")

    def will_unmount(self):
        self.on_destroy()

    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.title = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            width=300
        )
        self.downloads_badge = ft.Badge(label="", bgcolor=ft.Colors.PRIMARY)
        self.downloads_button = ft.IconButton(ft.Icons.DOWNLOAD, on_click=self.go_to_downloads_center)
        self.actions = [
            self.downloads_button,
            ft.IconButton(ft.Icons.ACCOUNT_CIRCLE, on_click=self.go_to_auth_management),
            ft.IconButton(ft.Icons.SETTINGS, on_click=self.go_to_settings),
        ]
        self.token_expires_in = None
        self.manager = manager
        self.bgcolor = ft.Colors.SURFACE_CONTAINER
        self.alive = True
        self.upd_task = asyncio.create_task(self.update_task())

    def on_destroy(self):
        self.alive = False
        self.upd_task.cancel()

    async def update_task(self):
        self.token_expires_in = await AuthorizationProvider.get_token_valid_to()
        while self.alive:
            count_downloads = self.manager.total_tasks
            if count_downloads > 0:
                self.downloads_badge.label = str(count_downloads)
                self.downloads_button.badge = self.downloads_badge
            else:
                self.downloads_badge.badge = None
            if self.token_expires_in and datetime.datetime.now(datetime.timezone.utc) < self.token_expires_in:
                self.title.controls = [
                    ft.Icon(ft.Icons.SPELLCHECK, color=ft.Colors.ON_SURFACE_VARIANT),
                ]
            else:
                self.title.controls = [
                    ft.Icon(ft.Icons.MONEY_OFF, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Icon(ft.Icons.MUSIC_OFF, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Icon(ft.Icons.FOLDER_OFF, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(
                        "No authorization",
                        size=20,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        tooltip=ft.Tooltip(
                            message="To watch and download private content available to you, log in the app (button on the right)",
                            mouse_cursor=ft.MouseCursor.CLICK
                        )
                    ),
                ]
            self.update()
            await asyncio.sleep(1)
