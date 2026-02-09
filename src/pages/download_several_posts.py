import datetime

import flet as ft

import components
from core.downloads_manager import DownloadManager
from core.utils import parse_author_link


class DownloadSeveralPostsPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.manager = manager
        self.route = "/download-several-posts"
        self.text_field = ft.TextField(
            prefix_icon=ft.IconButton(ft.Icons.ACCOUNT_CIRCLE, on_click=self.parse_clipboard_content),
            hint_text="https://boosty.to/author",
            width=450,
            value="",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        )
        today = datetime.datetime.now()
        self.parse_from = datetime.datetime(year=today.year, month=today.month, day=today.day - 3)
        self.parse_to = datetime.datetime(year=today.year, month=today.month, day=today.day)
        self.date_range_picker = ft.DateRangePicker(
            start_value=self.parse_from,
            end_value=self.parse_to,
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
            on_change=self.handle_date_picker_change,
            first_date=datetime.datetime(today.year - 10, 1, 1),
            last_date=self.parse_to,
        )
        self.date_from_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
        self.date_to_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
        self.status_text = ft.Text(
            "Searching posts by your criteria...",
            size=16,
            weight=ft.FontWeight.W_600,
        )
        self.description_text = ft.Text(
            "0 posts found",
            size=12,
            weight=ft.FontWeight.W_400,
        )
        self.progress_container = ft.Container(
            visible=False,
            content=ft.Row(
                controls=[
                    ft.ProgressRing(
                        width=40,
                        height=40,
                        stroke_width=2,
                    ),
                    ft.Column(
                        spacing=2,
                        controls=[
                            self.status_text,
                            self.description_text,
                        ],
                    ),
                ],
                spacing=16,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            padding=ft.padding.all(16),
            border_radius=ft.border_radius.all(12),
        )
        self.controls = [
            components.AppBar(manager),
            ft.Row(controls=[
                ft.IconButton(ft.Icon(ft.Icons.ARROW_BACK), on_click=self.go_to_index),
                ft.Text("Download several posts", size=24, weight=ft.FontWeight.BOLD),
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
                        ft.Text("Download posts published at:"),
                        ft.Row([
                            self.date_from_text,
                            ft.Text("—", size=20),
                            self.date_to_text,
                            ft.IconButton(
                                ft.Icon(ft.Icons.EDIT_CALENDAR_ROUNDED, size=20),
                                on_click=lambda x: self.page.show_dialog(self.date_range_picker),
                            ),
                        ], alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Button(
                            content=ft.Text("Download", size=17),
                            icon=ft.Icon(ft.Icons.DOWNLOAD, color=ft.Colors.PRIMARY, size=16),
                            height=50,
                            width=150,
                            color=ft.Colors.ON_SURFACE,
                            on_click=self.download_posts,
                        ),
                        self.progress_container
                    ]
                )
            )
        ]

    async def parse_clipboard_content(self):
        clipboard = await ft.Clipboard().get()
        if clipboard:
            author_name = parse_author_link(clipboard)
            if author_name:
                self.text_field.value = author_name
                self.page.update()

    def build(self):
        self.update_ranges()

    def update_ranges(self):
        self.date_from_text.value = self.parse_from.strftime("%d.%m.%Y")
        self.date_to_text.value = self.parse_to.strftime("%d.%m.%Y")
        self.page.update()

    async def go_to_index(self):
        await self.page.push_route("/")

    def handle_date_picker_change(self, e: ft.Event[ft.DateRangePicker]):
        self.parse_from = e.control.start_value
        self.parse_to = e.control.end_value
        self.update_ranges()

    async def download_posts(self):
        if self.text_field.value.strip() == "":
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Empty author"),
                    content=ft.Text("Type link to author's page or author's nickname"),
                    actions=[ft.TextButton("Wow, i'll", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return