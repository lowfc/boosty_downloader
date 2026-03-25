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
                content=ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=50,
                    controls=[
                        ft.Image(
                            src="main-page-logo.svg",
                            width=205,
                            height=64,
                        ),
                        ft.Row(
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
                                                            ft.Text(
                                                                value="One post",
                                                                size=20,
                                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                                            ),
                                                            ft.Text(
                                                                value="download a specific author's post via a direct link",
                                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                                            ),
                                                        ],
                                                    ),
                                                ),
                                            ],
                                        )
                                    ),
                                    on_click=self.go_to_download_post,
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
                                                            ft.Text(
                                                                value="Several posts",
                                                                size=20,
                                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                                            ),
                                                            ft.Text(
                                                                value="download an author's posts over a given time period",
                                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                                            ),
                                                        ],
                                                    ),
                                                ),
                                            ],
                                        )
                                    ),
                                    on_click=self.go_to_mass_downloader,
                                ),
                            ],
                        ),
                        ft.PopupMenuButton(
                            content=ft.Container(
                                content=ft.Row(
                                    [
                                        ft.Icon(ft.Icons.MORE_HORIZ),
                                        ft.Text(
                                            "Instruments", align=ft.Alignment.CENTER
                                        ),
                                    ],
                                    width=120,
                                    alignment=ft.MainAxisAlignment.CENTER,
                                ),
                                padding=ft.Padding.all(5),
                            ),
                            items=[
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.MERGE),
                                            ft.Text("Merge author's content"),
                                        ]
                                    ),
                                    on_click=self.go_to_content_merger,
                                ),
                                ft.PopupMenuItem(
                                    content=ft.Row(
                                        [
                                            ft.Icon(ft.Icons.IMAGE),
                                            ft.Text("Download image by link"),
                                        ]
                                    ),
                                    on_click=self.go_to_media_downloader,
                                ),
                            ],
                            menu_position=ft.PopupMenuPosition.UNDER,
                        ),
                    ],
                ),
            ),
        ]

    async def go_to_download_post(self):
        await self.page.push_route("/download-post")

    async def go_to_content_merger(self):
        await self.page.push_route("/merge-author-content")

    async def go_to_media_downloader(self):
        await self.page.push_route("/download-media-by-link")

    async def go_to_mass_downloader(self):
        await self.page.push_route("/download-several-posts")
