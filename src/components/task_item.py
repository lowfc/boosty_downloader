import os
import subprocess
from typing import Optional, Callable, Awaitable

import flet as ft

from core.defs.tasks import TaskInfo, TASK_ERROR_STATUS_LINE


@ft.control
class TaskItem(ft.Container):

    def __init__(
        self,
        task_info: Optional[TaskInfo] = None,
        visible=False,
        on_cancel: Optional[Callable[[Optional[TaskInfo]], Awaitable]] = None,
        on_retry: Optional[Callable[[Optional[TaskInfo]], Awaitable]] = None,
    ):
        super().__init__()
        self.progress_bar = ft.ProgressBar(color=ft.Colors.ORANGE, height=5)
        self.display_subtitle = ft.Container(self.progress_bar, align=ft.Alignment.CENTER, expand=True)
        self.folder_open_button = ft.IconButton(
            ft.Icon(ft.Icons.FOLDER, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.open_task_folder,
            bgcolor=ft.Colors.PRIMARY,
        )
        self.stop_button = ft.IconButton(
            ft.Icon(ft.Icons.STOP, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.on_cancel,
            bgcolor=ft.Colors.PRIMARY,
        )
        self.retry_button = ft.IconButton(
            ft.Icon(ft.Icons.REFRESH, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.on_retry,
            bgcolor=ft.Colors.PRIMARY,
        )
        self.task_info = task_info
        if self.task_info:
            title = self.task_info.post_id
            author = self.task_info.author
        else:
            title = ""
            author = ""
        self.task_name = ft.Text(title, overflow=ft.TextOverflow.ELLIPSIS, expand=True)
        self.task_prefix = ft.Text(author, color=ft.Colors.SECONDARY, overflow=ft.TextOverflow.ELLIPSIS, weight=ft.FontWeight.W_500)
        self.task_weight = ft.Text("", color=ft.Colors.SECONDARY)
        self.top_row = ft.Row(
            [
                self.task_prefix,
                ft.Text("-"),
                self.task_name,
                self.task_weight,
            ], spacing=5, expand=True,
        )
        self.trailing_button = ft.Container(self.stop_button)
        self.display_task = ft.Row(
            [
                self.folder_open_button,
                ft.Column(
                    [self.top_row, self.display_subtitle],
                    spacing=1,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                self.trailing_button
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        self.path = None
        self.visible = visible
        self.on_cancel = on_cancel
        self.on_retry = on_retry
        self.update_view(self.task_info)

    def build(self):
        self.content = ft.Container(
            content=self.display_task,
            border_radius=5,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
            height=60,
            padding=10,
        )

    async def open_task_folder(self):
        if self.path and os.path.isdir(self.path):
            if self.page.platform == ft.PagePlatform.WINDOWS:
                subprocess.Popen(["explorer", self.path])
            elif self.page.platform in (ft.PagePlatform.LINUX, ft.PagePlatform.MACOS):
                await self.page.launch_url(f"file://{self.path}")

    def update_view(self, task_info: Optional[TaskInfo] = None, visible=False):
        self.visible = visible
        if not task_info:
            return
        self.task_info = task_info
        task_title = self.task_info.title or self.task_info.post_id
        task_prefix = self.task_info.author
        self.task_name.value = task_title
        self.task_prefix.value = task_prefix
        self.path = self.task_info.path
        if self.task_info.total_weight < 1024**3:
            weight = f"{self.task_info.total_weight / 1024 ** 2:.1f} MB"
        else:
            weight = f"{self.task_info.total_weight / 1024 ** 3:.1f} GB"
        self.task_weight.value = f"{self.task_info.count_files} files, {weight}"
        if self.task_info.finished:
            if self.task_info.error:
                err_icon, err_descr = TASK_ERROR_STATUS_LINE[self.task_info.error]
                self.display_subtitle.content = ft.Row(
                    controls=[
                        ft.Icon(
                            err_icon,
                            color=ft.Colors.RED,
                            align=ft.Alignment.CENTER_LEFT,
                            size=15,
                        ),
                        ft.Text(
                            err_descr,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ]
                )
                self.trailing_button.content = self.retry_button
                self.task_weight.value = ""
            else:
                self.display_subtitle.content = ft.Row(
                    controls=[
                        ft.Icon(
                            ft.Icons.DONE,
                            color=ft.Colors.GREEN,
                            align=ft.Alignment.CENTER_LEFT,
                            size=15,
                        ),
                        ft.Text(
                            "Complete",
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ]
                )
                self.trailing_button.content = None
        else:
            if self.display_subtitle.content != self.progress_bar:
                self.display_subtitle.content = self.progress_bar
                self.trailing_button.content = self.stop_button
            self.progress_bar.value = self.task_info.percent

    async def on_cancel(self):
        if self.on_cancel:
            await self.on_cancel(self.task_info)

    async def on_retry(self):
        if self.on_retry:
            await self.on_retry(self.task_info)
