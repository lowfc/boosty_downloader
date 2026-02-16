import asyncio
import datetime

import flet as ft

import components
from core.authorization_provider import AuthorizationProvider
from core.boosty.client import BoostyClient
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
        self.parse_from = datetime.datetime(year=today.year, month=today.month, day=today.day - 3, tzinfo=datetime.timezone.utc)
        self.parse_to = datetime.datetime(year=today.year, month=today.month, day=today.day, tzinfo=datetime.timezone.utc)
        self.date_range_picker = ft.DateRangePicker(
            start_value=self.parse_from,
            end_value=self.parse_to,
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
            on_change=self.handle_date_picker_change,
            first_date=datetime.datetime(today.year - 10, 1, 1, tzinfo=datetime.timezone.utc),
            last_date=self.parse_to,
        )
        self.date_from_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
        self.date_to_text = ft.Text("", size=20, weight=ft.FontWeight.BOLD)
        self.status_text = ft.Text(
            "Preparing...",
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
                                ft.Icon(ft.Icons.EDIT_CALENDAR, size=20),
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
        self.date_range_picker.start_value = self.parse_from
        self.date_range_picker.end_value =  self.parse_to
        self.page.update()

    async def go_to_index(self):
        await self.page.push_route("/")

    def handle_date_picker_change(self, e: ft.Event[ft.DateRangePicker]):
        self.parse_from = datetime.datetime(
            year=e.control.start_value.year,
            month=e.control.start_value.month,
            day=e.control.start_value.day,
            hour=0,
            minute=0,
            second=0,
            tzinfo=datetime.timezone.utc
        )
        self.parse_to = datetime.datetime(
            year=e.control.end_value.year,
            month=e.control.end_value.month,
            day=e.control.end_value.day,
            hour=23,
            minute=59,
            second=59,
            tzinfo=datetime.timezone.utc
        )
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
        self.progress_container.visible = True
        self.disabled = True
        self.page.update()
        await asyncio.sleep(.5)
        author_name = parse_author_link(self.text_field.value)
        auth_token = await AuthorizationProvider.get_authorization_if_valid()
        client = BoostyClient(
            chunk_size=3600,
            download_timeout=500,
            auth_token=auth_token,
        )
        max_int_id = await client.get_max_int_id(author_name)
        if not max_int_id:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Empty page"),
                    content=ft.Text("An error has occurred, or author have no posts. Please try again later."),
                    actions=[ft.TextButton("Ok", on_click=lambda e: self.page.pop_dialog())],
                    open=True,
                )
            )
            return

        self.status_text.value = "Searching posts by your criteria..."
        self.page.update()
        offset = f"{int(self.parse_to.timestamp())}:{max_int_id + 1}"
        left_border = int(self.parse_from.timestamp())
        prepared_posts = []
        run = True
        while run:
            post_list = await client.get_posts_list(author_name, offset=offset)
            offset = post_list.extra.offset

            for post in post_list.data:
                if post.publish_time >= left_border:
                    prepared_posts.append(post)
                else:
                    run = False

            if post_list.extra.is_last:
                run = False
            self.description_text.value = f"{len(prepared_posts)} posts found"
            self.page.update()
            await asyncio.sleep(.5)

        self.status_text.value = "Creating tasks in the manager"
        tasks_created = 0
        for post in prepared_posts:
            if await self.manager.add_task(author_name, post.id, post):
                tasks_created += 1
            await asyncio.sleep(.1)
            self.description_text.value = f"{tasks_created} tasks created"
            self.page.update()

        self.progress_container.visible = False
        self.disabled = False
        await asyncio.sleep(.5)
        self.page.update()
