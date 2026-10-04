import asyncio
from pathlib import Path

import aiofiles
import flet as ft

import __version__ as app_version
import components
from components.soft_layout import button_style, page_shell, soft_card, soft_icon
from core.downloads_manager import DownloadManager
from core.logger import setup_logger

logger = setup_logger()


class FeedbackAndBugsPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/feedback-and-bugs"
        self.padding = self.spacing = 0
        self.active = True
        self.load_task = None
        self.copy_task = None
        self.log_text = ft.Text("", size=12, font_family="monospace", selectable=True)
        self.logs_field = ft.Container(
            ft.Column([self.log_text], scroll=ft.ScrollMode.AUTO, spacing=0),
            bgcolor=ft.Colors.SURFACE,
            border_radius=9,
            padding=16,
            height=220,
            visible=False,
        )
        self.details_button = ft.TextButton(
            "View diagnostic details",
            icon=ft.Icons.KEYBOARD_ARROW_DOWN,
            on_click=self.toggle_details,
            style=ft.ButtonStyle(
                color=ft.Colors.ON_SURFACE_VARIANT,
                padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                shape=ft.RoundedRectangleBorder(radius=8),
                text_style=ft.TextStyle(size=12),
            ),
        )
        self.device_text = ft.Text(
            "Loading device information…",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
            expand=True,
        )
        self.copy_button = ft.Button(
            "Copy diagnostics",
            icon=ft.Icons.CONTENT_COPY,
            height=42,
            style=button_style(primary=True),
            on_click=self.copy_log,
            disabled=True,
        )
        self.copy_help = ft.Text(
            "Then paste them into your GitHub issue.",
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.copy_error = ft.Text("", size=12, color=ft.Colors.ERROR, visible=False)
        self.discussion_card = self.contact_card(
            "Share an idea",
            "Suggest a feature, ask a question, or tell us what could be better.",
            "Start a discussion",
            ft.Icons.CHAT_BUBBLE_OUTLINE,
            "/discussions/new/choose",
        )
        self.issue_card = self.contact_card(
            "Report a bug",
            "Describe what happened and the steps to reproduce it. Include diagnostics below.",
            "Create an issue",
            ft.Icons.BUG_REPORT_OUTLINED,
            "/issues/new",
        )
        self.diagnostics_card = soft_card(
            ft.Column(
                spacing=16,
                controls=[
                    ft.Row(
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        controls=[
                            ft.Icon(
                                ft.Icons.DESCRIPTION_OUTLINED,
                                size=20,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                            ft.Column(
                                expand=True,
                                spacing=4,
                                controls=[
                                    ft.Text(
                                        "Diagnostic information",
                                        size=15,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        "Attach this to your bug report to help us find the cause.",
                                        size=13,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.ResponsiveRow(
                        spacing=12,
                        run_spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text(
                                f"Version {app_version.VERSION} · build {app_version.BUILD}",
                                size=12,
                                col={"xs": 12, "md": 3},
                            ),
                            ft.Row(
                                spacing=7,
                                col={"xs": 12, "md": 5},
                                controls=[
                                    ft.Icon(
                                        ft.Icons.DESKTOP_WINDOWS_OUTLINED,
                                        size=16,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    self.device_text,
                                ],
                            ),
                            ft.Container(
                                self.details_button,
                                alignment=ft.Alignment.CENTER_RIGHT,
                                col={"xs": 12, "md": 4},
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT),
                    self.logs_field,
                    ft.Row(
                        wrap=True,
                        spacing=16,
                        run_spacing=10,
                        controls=[self.copy_button, self.copy_help],
                    ),
                    self.copy_error,
                ],
            ),
            padding=24,
        )
        self.toolbar = components.AppBar(manager)
        self.controls = [
            page_shell(
                self.toolbar,
                ft.Column(
                    spacing=20,
                    controls=[
                        ft.Column(
                            spacing=6,
                            controls=[
                                ft.Text(
                                    "Feedback and bugs",
                                    size=24,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    "Share an idea or help us fix something that isn't working.",
                                    size=13,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                        ft.ResponsiveRow(
                            [self.discussion_card, self.issue_card],
                            spacing=16,
                            run_spacing=16,
                        ),
                        self.diagnostics_card,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=7,
                            controls=[
                                ft.Icon(
                                    ft.Icons.OPEN_IN_NEW,
                                    size=14,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                                ft.Text(
                                    "Discussions and issues open on GitHub.",
                                    size=12,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                    ],
                ),
                ft.Text(
                    f"{app_version.NAME} · {app_version.VERSION}",
                    size=11,
                    expand=True,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Icons.INFO_OUTLINE,
                self.open_project,
                width=744,
                footer_action_label="Project on GitHub",
            )
        ]

    @staticmethod
    def contact_card(title, description, action, icon, url_path):
        card = soft_card(
            ft.Column(
                spacing=0,
                tight=True,
                controls=[
                    soft_icon(icon, 40),
                    ft.Container(height=16),
                    ft.Text(title, size=17, weight=ft.FontWeight.W_500),
                    ft.Container(height=6),
                    ft.Text(description, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Container(height=22),
                    ft.TextButton(
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text(action, size=13, weight=ft.FontWeight.W_500),
                                ft.Icon(ft.Icons.NORTH_EAST, size=16),
                            ],
                        ),
                        url=ft.Url(app_version.URL + url_path, ft.UrlTarget.BLANK),
                        style=ft.ButtonStyle(
                            color=ft.Colors.PRIMARY,
                            padding=ft.Padding.symmetric(horizontal=10, vertical=8),
                            shape=ft.RoundedRectangleBorder(radius=8),
                            text_style=ft.TextStyle(size=13),
                        ),
                    ),
                ],
            ),
            padding=24,
        )
        card.col = {"xs": 12, "md": 6}
        return card

    def refresh(self):
        if self.active:
            self.update()

    def did_mount(self):
        self.load_task = asyncio.create_task(self.get_app_info())

    def will_unmount(self):
        self.active = False
        for task in (self.load_task, self.copy_task):
            if task and not task.done():
                task.cancel()

    def toggle_details(self, e=None):
        self.logs_field.visible = not self.logs_field.visible
        self.details_button.content = (
            "Hide diagnostic details"
            if self.logs_field.visible
            else "View diagnostic details"
        )
        self.details_button.icon = (
            ft.Icons.KEYBOARD_ARROW_UP
            if self.logs_field.visible
            else ft.Icons.KEYBOARD_ARROW_DOWN
        )
        self.refresh()

    async def get_device_info(self) -> str:
        try:
            device_info = await self.page.get_device_info()
        except Exception:
            logger.exception("Could not load diagnostic device information")
            return "Device information unavailable"
        if isinstance(device_info, ft.MacOsDeviceInfo):
            return (
                f"macOS {device_info.major_version}.{device_info.minor_version}."
                f"{device_info.patch_version} · {device_info.arch}"
            )
        if isinstance(device_info, ft.WindowsDeviceInfo):
            return f"{device_info.product_name} {device_info.edition_id}"
        if isinstance(device_info, ft.LinuxDeviceInfo):
            return device_info.pretty_name
        return "Unknown device"

    async def get_app_info(self):
        device_info = await self.get_device_info()
        try:
            async with aiofiles.open(
                Path("runtime.log"), mode="r", encoding="utf-8", errors="replace"
            ) as log:
                current_log = await log.read()
        except FileNotFoundError:
            current_log = "No run log available."
        except OSError:
            logger.exception("Could not read diagnostic log")
            current_log = "Run log unavailable."
        if not self.active:
            return
        self.device_text.value = device_info
        self.log_text.value = (
            f"App version: v{app_version.VERSION} (build {app_version.BUILD})\n"
            f"{device_info}\n\nLast run log:\n{current_log}"
        )
        self.copy_button.disabled = False
        self.refresh()

    async def copy_log(self, e=None):
        if self.copy_button.disabled or not self.active:
            return
        if self.copy_task and not self.copy_task.done():
            self.copy_task.cancel()
        self.copy_button.disabled = True
        self.copy_error.visible = False
        self.refresh()
        try:
            await ft.Clipboard().set(self.log_text.value)
        except Exception:
            logger.exception("Could not copy diagnostics")
            self.copy_button.content = "Copy diagnostics"
            self.copy_button.icon = ft.Icons.CONTENT_COPY
            self.copy_help.value = "Then paste them into your GitHub issue."
            self.copy_error.value = "Couldn't copy diagnostics. Please try again."
            self.copy_error.visible = True
        else:
            if not self.active:
                return
            self.copy_button.content = "Copied"
            self.copy_button.icon = ft.Icons.CHECK
            self.copy_help.value = "Ready to paste into your GitHub issue."
            self.copy_task = asyncio.create_task(self.reset_copy_button())
        finally:
            self.copy_button.disabled = False
            self.refresh()

    async def reset_copy_button(self):
        await asyncio.sleep(2)
        if not self.active:
            return
        self.copy_button.content = "Copy diagnostics"
        self.copy_button.icon = ft.Icons.CONTENT_COPY
        self.copy_help.value = "Then paste them into your GitHub issue."
        self.refresh()

    async def open_project(self, e=None):
        await ft.UrlLauncher().launch_url(app_version.URL)
