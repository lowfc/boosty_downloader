import flet as ft

import components
from core.downloads_manager import DownloadManager
from core.utils import parse_post_link


class DownloadPostPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self.route = "/download-post"
        self.text_field = ft.TextField(
            prefix_icon=ft.IconButton(ft.Icons.LINK, on_click=self.parse_clipboard_link),
            hint_text="https://boosty.to/author/posts/dba61f8b-d6dd-4105-9d00-db1c46f13946",
            width=615,
            value="",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        )
        self.controls = [
            components.AppBar(self.manager),
            ft.Row(controls=[
                ft.IconButton(ft.Icon(ft.Icons.ARROW_BACK), on_click=self.go_to_index),
                ft.Text("Download post", size=24, weight=ft.FontWeight.BOLD),
            ]),
            ft.Container(
                alignment=ft.Alignment.CENTER,
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=15,
                    controls=[
                        self.text_field,
                        ft.Button(
                            content=ft.Text("Download", size=17),
                            icon=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.PRIMARY, size=16),
                            height=50,
                            width=150,
                            color=ft.Colors.ON_SURFACE,
                            on_click=self.download_post,
                        )
                    ]
                )
            )
        ]

    async def parse_clipboard_link(self):
        clipboard = await ft.Clipboard().get()
        if clipboard:
            post_info = parse_post_link(clipboard)
            if post_info:
                self.text_field.value = post_info.generate_url()
                self.page.update()
                await self.download_post()

    async def go_to_index(self):
        await self.page.push_route("/")

    async def download_post(self):
        if self.text_field.value.strip() == "":
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Empty address"),
                    content=ft.Text("Type link to post into the text field"),
                    actions=[ft.TextButton("Ops, ok", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return
        rel_post_link = parse_post_link(self.text_field.value)
        if not rel_post_link:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Link to post seems invalid"),
                    content=ft.Text("It looks like you entered an incorrect link"),
                    actions=[ft.TextButton("I'll check", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return
        self.text_field.value = ""
        self.page.update()
        add_result = await self.manager.add_task(rel_post_link.author, rel_post_link.id)
        if add_result:
            self.page.show_dialog(ft.SnackBar(ft.Text("Queued")))
        else:
            self.page.show_dialog(ft.SnackBar(ft.Text("Already in queue")))
