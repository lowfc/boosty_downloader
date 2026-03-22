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
        visible = False,
        on_cancel: Optional[Callable[[Optional[TaskInfo]], Awaitable]] = None,
        on_retry: Optional[Callable[[Optional[TaskInfo]], Awaitable]] = None,
    ):
        super().__init__()
        self.display_subtitle = ft.ProgressBar(color=ft.Colors.ORANGE)
        self.folder_open_button = ft.IconButton(
            ft.Icon(ft.Icons.FOLDER, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.open_task_folder,
            bgcolor=ft.Colors.PRIMARY
        )
        self.stop_button = ft.IconButton(
            ft.Icon(ft.Icons.STOP, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.on_cancel,
            bgcolor=ft.Colors.PRIMARY
        )
        self.retry_button = ft.IconButton(
            ft.Icon(ft.Icons.REFRESH, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.on_retry,
            bgcolor=ft.Colors.PRIMARY
        )
        self.task_info = task_info
        if self.task_info:
            title = f"{self.task_info.author} / {self.task_info.post_id}"
        else:
            title = ""
        self.task_name = ft.Text(title)
        self.task_weight = ft.Text("", color=ft.Colors.SECONDARY)
        self.display_task = ft.ListTile(
            leading=self.folder_open_button,
            trailing=self.stop_button,
            title=ft.Row(
                controls=[
                    self.task_name,
                    self.task_weight,
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                expand=True,
            ),
            subtitle=self.display_subtitle,
        )
        self.path = None
        self.visible = visible
        self.on_cancel = on_cancel
        self.on_retry = on_retry
        self.update_view(self.task_info)

    def build(self):
        self.content = ft.Container(
            content=self.display_task,
            border_radius=10,
            bgcolor=ft.Colors.SURFACE_CONTAINER_LOW,
        )

    async def open_task_folder(self):
        if self.path and os.path.isdir(self.path):
            await self.page.launch_url(f"file://{self.path}")

    def update_view(self, task_info: Optional[TaskInfo] = None, visible = False):
        self.visible = visible
        if not task_info:
            return
        self.task_info = task_info
        if self.task_info.title:
            self.task_name.value = self.task_info.title
        else:
            self.task_name.value = f"{self.task_info.author} / {self.task_info.post_id}"
        self.path = self.task_info.path
        if self.task_info.total_weight < 1024 ** 3:
            weight = f"{self.task_info.total_weight / 1024 ** 2:.1f} MB"
        else:
            weight = f"{self.task_info.total_weight / 1024 ** 3:.1f} GB"
        self.task_weight.value = f"{self.task_info.count_files} files, {weight}"
        if self.task_info.finished:
            if self.task_info.error:
                err_icon, err_descr = TASK_ERROR_STATUS_LINE[self.task_info.error]
                self.display_task.subtitle = ft.Row(
                    controls=[
                        ft.Icon(err_icon, color=ft.Colors.RED, align=ft.Alignment.CENTER_LEFT, size=15),
                        ft.Text(err_descr, weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT),
                    ]
                )
                self.display_task.trailing = self.retry_button
                self.task_weight.value = ""
            else:
                self.display_task.subtitle = ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.DONE, color=ft.Colors.GREEN, align=ft.Alignment.CENTER_LEFT, size=15),
                        ft.Text("Complete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT),
                    ]
                )
                self.display_task.trailing = None
        else:
            if self.display_task.subtitle != self.display_subtitle:
                self.display_task.subtitle = self.display_subtitle
                self.display_task.trailing = self.stop_button
            self.display_subtitle.value = self.task_info.percent

    async def on_cancel(self):
        if self.on_cancel:
            await self.on_cancel(self.task_info)

    async def on_retry(self):
        if self.on_retry:
            await self.on_retry(self.task_info)
