import asyncio

import flet as ft

import components
from core.downloads_manager import DownloadManager


class WelcomePage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/"
        self.controls = [
            components.AppBar(manager),
            ft.Container(
                alignment=ft.Alignment.CENTER,
                expand=True,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Button(
                            content=ft.Container(
                                content=ft.Row(
                                    width=450,
                                    height=110,
                                    controls=[
                                        ft.Icon(ft.Icons.DOWNLOAD, size=30),
                                        ft.Container(
                                            padding=ft.Padding.all(10),
                                            content=ft.Column(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=2,
                                                controls=[
                                                    ft.Text(value="Download post", size=20,
                                                            color=ft.Colors.ON_SURFACE_VARIANT),
                                                    ft.Text(value="download a specific author's post via a direct link",
                                                            color=ft.Colors.ON_SURFACE_VARIANT),
                                                ],
                                            ),
                                        ),
                                    ]
                                )
                            ),
                            on_click=lambda e: asyncio.create_task(self.go_to_download_post()),
                        ),
                        ft.Button(
                            content=ft.Container(
                                content=ft.Row(
                                    width=450,
                                    height=110,
                                    controls=[
                                        ft.Icon(ft.Icons.CONTACTS, size=30),
                                        ft.Container(
                                            padding=ft.Padding.all(10),
                                            content=ft.Column(
                                                alignment=ft.MainAxisAlignment.CENTER,
                                                spacing=2,
                                                controls=[
                                                    ft.Text(value="View posts", size=20,
                                                            color=ft.Colors.ON_SURFACE_VARIANT),
                                                    ft.Text(
                                                        value="view all author's posts and download the necessary ones",
                                                        color=ft.Colors.ON_SURFACE_VARIANT),
                                                ],
                                            ),
                                        ),
                                    ]
                                )
                            )
                        ),
                    ]
                )
            )
        ]

    async def go_to_download_post(self):
        await self.page.push_route("/download-post")