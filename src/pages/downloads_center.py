import asyncio

import flet as ft

import components
from components.paginator import Paginator
from components.soft_layout import button_style, page_shell, soft_icon
from components.task_item import TaskItem
from core.defs.tasks import TaskInfo
from core.downloads_manager import DownloadManager
from core.utils import get_destination_folder
from localization import Localizer


class DownloadsCenterPage(ft.View):
    def __init__(self, manager: DownloadManager, localizer=None):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.route = "/downloads-center"
        self.padding = 0
        self.spacing = 0
        self.manager = manager
        self.upd_task = None
        self.count_slots = 10
        self.slots = [
            TaskItem(
                on_cancel=self.on_task_cancel,
                on_retry=self.on_task_retry,
                localizer=self.localizer,
            )
            for _ in range(self.count_slots)
        ]
        self.list_view = ft.Column(controls=self.slots, spacing=12, visible=False)
        self.paginator = Paginator(
            items_per_page=self.count_slots, localizer=self.localizer
        )
        self.paginator.visible = False
        self.summary = ft.Text("", size=13, color=ft.Colors.ON_SURFACE_VARIANT)
        self.stop_all_button = ft.OutlinedButton(
            self.tr("Cancel all"),
            icon=ft.Icons.STOP_OUTLINED,
            style=button_style(),
            on_click=self.on_all_tasks_cancel,
            visible=False,
        )
        self.empty_view = ft.Container(
            padding=ft.Padding.symmetric(vertical=60),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=14,
                controls=[
                    soft_icon(ft.Icons.DOWNLOAD_OUTLINED, 60),
                    ft.Text(
                        self.tr("No downloads yet"), size=20, weight=ft.FontWeight.W_500
                    ),
                    ft.Text(
                        self.tr(
                            "Choose a post or an author's collection to get started."
                        ),
                        size=13,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=4),
                    ft.Button(
                        self.tr("Back to home"),
                        on_click=self.go_to_index,
                        style=button_style(primary=True),
                    ),
                ],
            ),
        )
        self.folder_note = ft.Text(
            self.tr("Download folder"),
            expand=True,
            size=11,
            overflow=ft.TextOverflow.ELLIPSIS,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        body = ft.Column(
            spacing=20,
            controls=[
                ft.Row(
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=5,
                            controls=[
                                ft.Text(
                                    self.tr("Downloads"),
                                    size=24,
                                    weight=ft.FontWeight.W_500,
                                ),
                                self.summary,
                            ],
                        ),
                        self.stop_all_button,
                    ],
                ),
                self.empty_view,
                self.list_view,
                self.paginator,
            ],
        )
        self.controls = [
            page_shell(
                components.AppBar(manager, localizer=self.localizer),
                body,
                self.folder_note,
                ft.Icons.FOLDER_OUTLINED,
                self.go_to_feedback,
                width=744,
                localizer=self.localizer,
            )
        ]

    def did_mount(self):
        self.upd_task = asyncio.create_task(self.update_task())

    def will_unmount(self):
        if self.upd_task:
            self.upd_task.cancel()

    async def go_to_index(self, e=None):
        await self.page.push_route("/")

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")

    async def on_all_tasks_cancel(self, e=None):
        await self.manager.stop_running_tasks()

    async def on_task_cancel(self, task_info: TaskInfo | None):
        if task_info:
            await self.manager.stop_task(task_info.post_id)

    async def on_task_retry(self, task_info: TaskInfo | None):
        if task_info:
            await self.manager.retry_task(task_info.post_id)

    async def refresh_tasks(self):
        self.paginator.set_total_items(self.manager.total_tasks)
        tasks = await self.manager.get_tasks(
            self.count_slots, offset=self.paginator.get_current_offset(), reverse=True
        )
        running = await self.manager.get_pending_tasks_count()
        active = await self.manager.get_active_tasks_count()
        self.summary.value = (
            self.tr(
                "{running} downloading · {queued} queued",
                running=running,
                queued=max(0, active - running),
            )
            if active
            else self.localizer.plural("count.downloads", self.manager.total_tasks)
        )
        self.summary.visible = bool(self.manager.total_tasks)
        self.stop_all_button.visible = active > 0
        self.empty_view.visible = not self.manager.total_tasks
        self.list_view.visible = bool(self.manager.total_tasks)
        for index, slot in enumerate(self.slots):
            (
                slot.update_view(tasks[index], visible=True)
                if index < len(tasks)
                else slot.update_view(visible=False)
            )

    async def update_task(self):
        folder = await get_destination_folder()
        self.folder_note.value = (
            str(folder) if folder else self.tr("Download folder unavailable")
        )
        self.folder_note.tooltip = self.folder_note.value
        while True:
            await self.refresh_tasks()
            self.update()
            await asyncio.sleep(0.3)
