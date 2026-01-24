import os
import subprocess

import flet as ft


@ft.control
class TaskItem(ft.Container):

    def __init__(self, author, post_id, percent = 0.0, visible = False):
        super().__init__()
        self.display_subtitle = ft.ProgressBar(color=ft.Colors.ORANGE)
        self.folder_open_button = ft.IconButton(
            ft.Icon(ft.Icons.FOLDER, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.open_task_folder,
            bgcolor=ft.Colors.PRIMARY
        )
        self.variant_button = ft.IconButton(
            ft.Icon(ft.Icons.STOP, color=ft.Colors.SURFACE_CONTAINER_LOW),
            on_click=self.open_task_folder,
            bgcolor=ft.Colors.PRIMARY
        )
        self.display_task = ft.ListTile(
            leading=self.folder_open_button,
            trailing=self.variant_button,
            title=f"{author} / {post_id}",
            subtitle=self.display_subtitle,
        )
        self.path = None
        self.update_view(author, post_id, percent, visible)

    def build(self):
        self.content = self.display_task

    async def open_task_folder(self):
        if self.path and os.path.isdir(self.path):
            subprocess.Popen(['explorer', self.path])

    def update_view(
        self,
        author = None,
        post_id = None,
        percent = None,
        title = None,
        path = None,
        visible = False,
    ):
        if title:
            self.display_task.title = title
        else:
            self.display_task.title = f"{author} / {post_id}"
        self.path = path
        if percent is not None and percent >= 1:
            self.display_task.subtitle = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DONE, color=ft.Colors.GREEN, align=ft.Alignment.CENTER_LEFT, size=15),
                    ft.Text("Complete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT),
                ]
            )
            self.display_task.trailing = None
        else:
            self.display_subtitle.value = percent
        self.visible = visible
