import flet as ft


@ft.control
class TaskItem(ft.Container):

    def __init__(self, author, post_id, percent = 0.0, visible = False):
        super().__init__()
        self.display_subtitle = ft.ProgressBar(color=ft.Colors.ORANGE)
        self.display_task = ft.ListTile(
            leading=ft.IconButton(ft.Icons.FOLDER),
            title=f"{author} / {post_id}",
            subtitle=self.display_subtitle,
        )
        self.update_view(author, post_id, percent, visible)

    def build(self):
        self.content = self.display_task

    def update_view(self, author = None, post_id = None, percent = None, visible = False):
        self.display_task.title = f"{author} / {post_id}"
        if percent is not None and percent >= 1:
            self.display_task.subtitle = ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DONE, color=ft.Colors.GREEN, align=ft.Alignment.CENTER_LEFT, size=15),
                    ft.Text("Complete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE_VARIANT),
                ]
            )
        else:
            self.display_subtitle.value = percent
        self.visible = visible
