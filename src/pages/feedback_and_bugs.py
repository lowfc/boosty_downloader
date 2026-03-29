import asyncio
from pathlib import Path

import flet as ft

import components
from core.downloads_manager import DownloadManager
import __version__ as app_version


class FeedbackAndBugsPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/feedback-and-bugs"
        self.manager = manager

        self.log_text = ft.Text("", selectable=True)
        self.logs_field = ft.Row(
            controls=[
                ft.Container(
                    self.log_text,
                    bgcolor=ft.Colors.SURFACE_CONTAINER,
                    border_radius=5,
                    padding=10,
                    expand=True,
                    height=300,
                )
            ],
            height=300,
        )
        self.copy_button = ft.Button(
            "Copy diagnostic",
            icon=ft.Icon(ft.Icons.COPY, color=ft.Colors.PRIMARY),
            color=ft.Colors.ON_SURFACE,
            height=45,
            on_click=self.copy_log,
        )
        self.controls = [
            components.AppBar(manager),
            ft.Row(
                controls=[
                    ft.IconButton(
                        ft.Icon(ft.Icons.ARROW_BACK), on_click=self.go_to_index
                    ),
                    ft.Text("Feedback and bugs", size=24, weight=ft.FontWeight.BOLD),
                ]
            ),
            ft.Column(
                spacing=10,
                controls=[
                    ft.Text(
                        "If you'd like to leave feedback about the app or suggest a new feature, "
                        "please create a discussion thread in the project repository:"
                    ),
                    ft.Row(
                        spacing=5,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.LINK, size=18, color=ft.Colors.PRIMARY),
                            ft.Text(
                                spans=[
                                    ft.TextSpan(
                                        "New project discussion",
                                        url=app_version.URL + "/discussions/new/choose",
                                        style=ft.TextStyle(
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.PRIMARY,
                                            decoration=ft.TextDecoration.UNDERLINE,
                                            size=15,
                                        ),
                                    )
                                ]
                            ),
                        ],
                    ),
                    ft.Text(
                        "If you encounter a bug, please report it in the project issues section:"
                    ),
                    ft.Row(
                        spacing=5,
                        controls=[
                            ft.Icon(ft.Icons.LINK, size=18, color=ft.Colors.PRIMARY),
                            ft.Text(
                                spans=[
                                    ft.TextSpan(
                                        "New project issue",
                                        url=app_version.URL + "/issues/new",
                                        style=ft.TextStyle(
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.PRIMARY,
                                            decoration=ft.TextDecoration.UNDERLINE,
                                            size=15,
                                        ),
                                    )
                                ]
                            ),
                        ],
                    ),
                    ft.Column(
                        [
                            ft.Text(
                                "To speed up the bug fix, please include diagnostic information with the issue:"
                            ),
                            self.logs_field,
                            self.copy_button,
                        ]
                    ),
                ],
            ),
        ]

    async def go_to_index(self):
        await self.page.push_route("/")

    def build(self):
        asyncio.create_task(self.get_app_info())

    async def get_device_info(self) -> str:
        try:
            device_info = await self.page.get_device_info()
        except Exception as e:
            print(e)
            return ""
        if isinstance(device_info, ft.MacOsDeviceInfo):
            os_info = f"macOS {device_info.os_release} {device_info.arch} {device_info.major_version}.{device_info.minor_version}"
        elif isinstance(device_info, ft.WindowsDeviceInfo):
            os_info = f"{device_info.product_name} {device_info.edition_id}"
        elif isinstance(device_info, ft.LinuxDeviceInfo):
            os_info = f"Linux {device_info.pretty_name} {device_info.version_id}"
        else:
            os_info = "Unknown device"
        return os_info

    async def get_app_info(self):
        log_path = Path("./runtime.log")
        current_log = ""
        if log_path.exists():
            with open(log_path, "r", encoding="utf-8") as f:
                current_log = f.read()
        diagnostic = (
            f"App version: v{app_version.VERSION} (build {app_version.BUILD})\n"
        )
        diagnostic += await self.get_device_info() + "\n"
        diagnostic += f"Last run log: \n{current_log}"
        self.log_text.value = diagnostic
        self.update()

    async def copy_log(self):
        await ft.Clipboard().set(self.log_text.value)
        self.copy_button.icon = ft.Icon(ft.Icons.DONE, color=ft.Colors.PRIMARY)
        self.page.update()
        await asyncio.sleep(1)
        self.copy_button.icon = ft.Icon(ft.Icons.COPY, color=ft.Colors.PRIMARY)
        self.page.update()
