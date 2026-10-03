import flet as ft

import components
from core.downloads_manager import DownloadManager
from themes import HOME_DARK_THEME, HOME_LIGHT_THEME


class WelcomePage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/"
        self.padding = 0
        self.spacing = 0
        self.auth_note = ft.Text(
            "Log in to download subscriber-only content.",
            size=11,
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=True,
        )
        self.toolbar = components.AppBar(manager, on_auth_change=self.update_auth_note)
        self.controls = [
            ft.Container(
                expand=True,
                bgcolor=ft.Colors.SURFACE,
                theme=HOME_LIGHT_THEME,
                dark_theme=HOME_DARK_THEME,
                content=ft.Column(
                    spacing=0,
                    controls=[
                        self.toolbar,
                        ft.Container(
                            expand=True,
                            alignment=ft.Alignment.CENTER,
                            padding=ft.Padding.symmetric(horizontal=32, vertical=24),
                            content=ft.Column(
                                width=696,
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                scroll=ft.ScrollMode.AUTO,
                                controls=[
                                    ft.Image(
                                        src="main-page-logo.svg", width=178, height=55
                                    ),
                                    ft.Container(height=24),
                                    ft.Text(
                                        "What would you like to download?",
                                        size=23,
                                        weight=ft.FontWeight.W_500,
                                        color=ft.Colors.ON_SURFACE,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Container(height=8),
                                    ft.Text(
                                        "Choose a single post or an author's collection.",
                                        size=13,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                        text_align=ft.TextAlign.CENTER,
                                    ),
                                    ft.Container(height=28),
                                    ft.ResponsiveRow(
                                        spacing=16,
                                        run_spacing=16,
                                        controls=[
                                            self.download_card(
                                                "One post",
                                                "Download a specific post\nby its direct link.",
                                                "Paste a link",
                                                ft.Icons.DOWNLOAD_OUTLINED,
                                                self.go_to_download_post,
                                            ),
                                            self.download_card(
                                                "Several posts",
                                                "Download an author's posts\nfor a selected period.",
                                                "Choose an author",
                                                ft.Icons.FILE_COPY_OUTLINED,
                                                self.go_to_mass_downloader,
                                            ),
                                        ],
                                    ),
                                    ft.Container(height=18),
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.CENTER,
                                        spacing=12,
                                        wrap=True,
                                        controls=[
                                            self.secondary_button(
                                                "Image by link",
                                                ft.Icons.IMAGE_OUTLINED,
                                                self.go_to_media_downloader,
                                            ),
                                            self.secondary_button(
                                                "Merge content",
                                                ft.Icons.MERGE,
                                                self.go_to_content_merger,
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ),
                        ft.Container(
                            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
                            border=ft.Border.only(
                                top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)
                            ),
                            content=ft.Row(
                                spacing=16,
                                controls=[
                                    ft.Row(
                                        expand=True,
                                        spacing=8,
                                        controls=[
                                            ft.Icon(
                                                ft.Icons.LOCK_OUTLINE,
                                                size=14,
                                                color=ft.Colors.ON_SURFACE_VARIANT,
                                            ),
                                            self.auth_note,
                                        ],
                                    ),
                                    self.secondary_button(
                                        "Feedback", None, self.go_to_feedback
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
            )
        ]

    @staticmethod
    def download_card(title, description, action, icon, on_click):
        return ft.Button(
            col={"xs": 12, "sm": 6},
            height=208,
            on_click=on_click,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
                color=ft.Colors.ON_SURFACE,
                shadow_color=ft.Colors.with_opacity(0.12, ft.Colors.ON_SURFACE),
                elevation={ft.ControlState.DEFAULT: 1, ft.ControlState.HOVERED: 3},
                side={
                    ft.ControlState.DEFAULT: ft.BorderSide(
                        1, ft.Colors.OUTLINE_VARIANT
                    ),
                    ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.PRIMARY),
                    ft.ControlState.FOCUSED: ft.BorderSide(1, ft.Colors.PRIMARY),
                },
                overlay_color=ft.Colors.with_opacity(0.04, ft.Colors.PRIMARY),
                shape=ft.RoundedRectangleBorder(radius=18),
                padding=23,
                animation_duration=180,
            ),
            content=ft.Column(
                spacing=0,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    ft.Container(
                        width=40,
                        height=40,
                        border_radius=11,
                        bgcolor=ft.Colors.PRIMARY_CONTAINER,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Icon(icon, size=22, color=ft.Colors.PRIMARY),
                    ),
                    ft.Container(height=16),
                    ft.Text(title, size=17, weight=ft.FontWeight.W_500),
                    ft.Container(height=6),
                    ft.Text(
                        description,
                        size=13,
                        weight=ft.FontWeight.W_400,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(height=18),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(
                                action,
                                size=12,
                                weight=ft.FontWeight.W_400,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Icon(
                                ft.Icons.ARROW_FORWARD, size=17, color=ft.Colors.PRIMARY
                            ),
                        ],
                    ),
                ],
            ),
        )

    @staticmethod
    def secondary_button(label, icon, on_click):
        return ft.TextButton(
            label,
            icon=ft.Icon(icon, size=15) if icon else None,
            on_click=on_click,
            style=ft.ButtonStyle(
                color={
                    ft.ControlState.DEFAULT: ft.Colors.ON_SURFACE_VARIANT,
                    ft.ControlState.HOVERED: ft.Colors.PRIMARY,
                },
                text_style=ft.TextStyle(size=12, weight=ft.FontWeight.W_400),
                padding=ft.Padding.symmetric(horizontal=8, vertical=8),
            ),
        )

    def update_auth_note(self, logged_in):
        self.auth_note.value = (
            "Subscriber-only content is available according to your subscriptions."
            if logged_in
            else "Log in to download subscriber-only content."
        )
        self.auth_note.update()

    async def go_to_download_post(self, e=None):
        await self.page.push_route("/download-post")

    async def go_to_content_merger(self, e=None):
        await self.page.push_route("/merge-author-content")

    async def go_to_media_downloader(self, e=None):
        await self.page.push_route("/download-media-by-link")

    async def go_to_mass_downloader(self, e=None):
        await self.page.push_route("/download-several-posts")

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")
