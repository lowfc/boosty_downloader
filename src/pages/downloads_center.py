import asyncio
from typing import List

import flet as ft

from src import components
from src.components.paginator import Paginator
from src.components.task_item import TaskItem
from src.core.downloads_manager import DownloadManager


class DownloadsCenterPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route="/downloads-center"
        self.list_view = ft.Column(spacing=10)
        self.count_slots = 10
        self.slots: List[TaskItem] = []
        self.paginator = Paginator(items_per_page=self.count_slots)
        self.manager = manager
        self.alive = True
        for i in range(self.count_slots):
            self.slots.append(
                TaskItem("", 0)
            )

        self.list_view.controls = self.slots

        self.controls = [
            components.AppBar(manager),
            ft.Column(
                controls=[
                    ft.Row(controls=[
                        ft.IconButton(ft.Icon(ft.Icons.ARROW_BACK),
                                      on_click=lambda e: asyncio.create_task(self.go_to_index())),
                        ft.Text("Downloads center", size=24, weight=ft.FontWeight.BOLD),
                    ]),
                    ft.Card(
                        shadow_color=ft.Colors.ON_SURFACE_VARIANT,
                        content=ft.Container(
                            padding=10,
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.DOWNLOADING),
                                title=ft.Text(
                                    f"In progress: 0 / 0"
                                ),
                            ),
                        ),
                    )
                ]
            ),
            ft.ListView(
                expand=True,
                controls=[
                    self.list_view,
                    self.paginator,
                ]
            )
        ]
        self.upd_task = asyncio.create_task(self.update_task())

    async def go_to_index(self):
        self.on_destroy()
        await self.page.push_route("/")

    def will_unmount(self):
        self.on_destroy()

    def on_destroy(self):
        self.alive = False
        self.upd_task.cancel()

    async def update_task(self):
        while self.alive:
            tasks = await self.manager.get_tasks(self.count_slots, offset=self.paginator.get_current_offset())
            self.paginator.set_total_items(self.manager.total_tasks)
            for slot_no in range(self.count_slots):
                if slot_no <= len(tasks) - 1:
                    self.slots[slot_no].update_view(
                        author=tasks[slot_no].author,
                        post_id=tasks[slot_no].post_id,
                        percent=tasks[slot_no].percent,
                        visible=True,
                    )
                else:
                    self.slots[slot_no].update_view()
                self.slots[slot_no].update()
            await asyncio.sleep(.1)
