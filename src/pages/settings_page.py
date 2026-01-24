import asyncio

import flet as ft

from src import components
from src.core.downloads_manager import DownloadManager


class SettingsPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/settings"
        self.controls = [
            components.AppBar(manager),
            ft.Row(controls=[
                ft.IconButton(ft.Icon(ft.Icons.ARROW_BACK), on_click=lambda e: asyncio.create_task(self.go_to_index())),
                ft.Text("Settings", size=24, weight=ft.FontWeight.BOLD),
            ]),
            components.SettingsGroup()
        ]

    async def go_to_index(self):
         await self.page.push_route("/")
