import asyncio
import os
from collections.abc import Awaitable, Callable
from pathlib import Path

import flet as ft

from components.soft_layout import soft_icon
from core.defs.tasks import TASK_ERROR_STATUS_LINE, TaskError, TaskInfo
from localization import Localizer


@ft.control
class TaskItem(ft.Container):
    def __init__(
        self,
        task_info: TaskInfo | None = None,
        visible=False,
        on_cancel: Callable[[TaskInfo | None], Awaitable] | None = None,
        on_retry: Callable[[TaskInfo | None], Awaitable] | None = None,
        localizer=None,
    ):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self._on_cancel = on_cancel
        self._on_retry = on_retry
        self.task_info = None
        self.path = None
        self.task_name = ft.Text(
            size=14,
            weight=ft.FontWeight.W_500,
            overflow=ft.TextOverflow.ELLIPSIS,
            expand=True,
        )
        self.task_metadata = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.status = ft.Text(size=12)
        self.detail = ft.Text(size=12, color=ft.Colors.ON_SURFACE_VARIANT, expand=True)
        self.progress_bar = ft.ProgressBar(
            height=4,
            color=ft.Colors.PRIMARY,
            bgcolor=ft.Colors.PRIMARY_CONTAINER,
            border_radius=2,
        )
        style = ft.ButtonStyle(
            color=ft.Colors.ON_SURFACE_VARIANT,
            text_style=ft.TextStyle(size=12),
            padding=0,
            visual_density=ft.VisualDensity.COMPACT,
        )
        self.stop_button = ft.TextButton(
            self.tr("Cancel"),
            icon=ft.Icons.CLOSE,
            height=24,
            style=style,
            on_click=self.on_cancel,
        )
        self.retry_button = ft.TextButton(
            self.tr("Retry"),
            icon=ft.Icons.REFRESH,
            height=24,
            style=style,
            on_click=self.on_retry,
        )
        self.folder_open_button = ft.TextButton(
            self.tr("Open folder"),
            height=24,
            icon=ft.Icons.FOLDER_OPEN_OUTLINED,
            style=style,
            on_click=self.open_task_folder,
        )
        self.trailing_button = ft.Container(self.stop_button)
        self.icon = soft_icon(ft.Icons.DOWNLOAD_OUTLINED)
        self.content = ft.Row(
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=14,
            controls=[
                self.icon,
                ft.Column(
                    expand=True,
                    spacing=5,
                    controls=[
                        ft.Row([self.task_name, self.status], spacing=12),
                        self.task_metadata,
                        self.progress_bar,
                        ft.Row([self.detail, self.trailing_button], spacing=12),
                    ],
                ),
            ],
        )
        self.padding = ft.Padding.symmetric(horizontal=18, vertical=14)
        self.border_radius = 18
        self.border = ft.Border.all(1, ft.Colors.OUTLINE_VARIANT)
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_LOWEST
        self.update_view(task_info, visible)

    async def open_task_folder(self, e=None):
        if self.path and os.path.isdir(self.path):
            if self.page.platform == ft.PagePlatform.WINDOWS:
                await asyncio.create_subprocess_exec("explorer", str(self.path))
            elif self.page.platform in (ft.PagePlatform.LINUX, ft.PagePlatform.MACOS):
                await ft.UrlLauncher().launch_url(Path(self.path).resolve().as_uri())

    def update_view(self, task_info: TaskInfo | None = None, visible=False):
        self.visible = visible
        if not task_info:
            self.task_info = None
            return
        self.task_info = task_info
        self.task_name.value = task_info.title or task_info.post_id
        self.path = task_info.path
        metadata = [task_info.author]
        if task_info.count_files:
            metadata.append(self.localizer.plural("count.files", task_info.count_files))
        if task_info.total_weight:
            divisor, unit = (
                (1024**3, self.tr("GB"))
                if task_info.total_weight >= 1024**3
                else (1024**2, self.tr("MB"))
            )
            metadata.append(f"{task_info.total_weight / divisor:.1f} {self.tr(unit)}")
        self.task_metadata.value = " · ".join(metadata)
        self.progress_bar.visible = not task_info.finished and task_info.running
        self.progress_bar.value = max(0, min(1, task_info.percent))
        self.status.color = ft.Colors.ON_SURFACE_VARIANT
        if task_info.finished:
            if task_info.error:
                cancelled = task_info.error == TaskError.CANCELLED
                self.status.value = (
                    self.tr("Cancelled") if cancelled else self.tr("Failed")
                )
                self.status.color = (
                    ft.Colors.ON_SURFACE_VARIANT if cancelled else ft.Colors.ERROR
                )
                self.detail.value = self.tr(TASK_ERROR_STATUS_LINE[task_info.error][1])
                self.icon.content.icon = (
                    ft.Icons.CLOSE if cancelled else ft.Icons.ERROR_OUTLINE
                )
                self.trailing_button.content = self.retry_button
            else:
                self.status.value = self.tr("Complete")
                self.status.color = ft.Colors.GREEN_600
                self.detail.value = self.tr("Saved to your download folder")
                self.icon.content.icon = ft.Icons.CHECK
                self.trailing_button.content = self.folder_open_button
                self.folder_open_button.disabled = not bool(
                    self.path and os.path.isdir(self.path)
                )
        else:
            self.status.value = (
                f"{self.progress_bar.value:.0%}"
                if task_info.running
                else self.tr("Queued")
            )
            self.detail.value = (
                self.tr("Downloading")
                if task_info.running
                else self.tr("Waiting to start")
            )
            self.icon.content.icon = (
                ft.Icons.DOWNLOAD_OUTLINED if task_info.running else ft.Icons.SCHEDULE
            )
            self.trailing_button.content = self.stop_button

    async def on_cancel(self, e=None):
        if self._on_cancel:
            await self._on_cancel(self.task_info)

    async def on_retry(self, e=None):
        if self._on_retry:
            await self._on_retry(self.task_info)
