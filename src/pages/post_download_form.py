import asyncio
import re
from pathlib import Path
from urllib.parse import urlparse

import flet as ft

import components
from components.soft_layout import button_style, page_shell, soft_card, soft_icon
from core.logger import setup_logger
from core.utils import get_destination_folder
from localization import Localizer

logger = setup_logger()


def author_from_input(value):
    value = value.strip()
    if "/" in value or ":" in value:
        try:
            url = urlparse(value if "://" in value else f"https://{value}")
        except ValueError:
            return None
        if url.scheme not in ("http", "https") or url.netloc.lower() != "boosty.to":
            return None
        value = url.path.strip("/")
    return value if re.fullmatch(r"[\w.-]+", value, flags=re.ASCII) else None


class PostDownloadForm(ft.View):
    """Shared form chrome and lifecycle for download entry points."""

    def __init__(self, manager, route, placeholder, on_submit, localizer=None):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.manager = manager
        self.route = route
        self.padding = self.spacing = 0
        self.active = True
        self.busy = False
        self.date_buttons = []
        self.folder_task = self.operation_task = None
        self.text_field = ft.TextField(
            value="",
            hint_text=placeholder,
            text_size=13,
            height=36,
            dense=True,
            filled=True,
            fill_color=ft.Colors.SURFACE,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT), border_radius=9
            ),
            autocorrect=False,
            enable_suggestions=False,
            on_submit=on_submit,
            on_change=self.clear_feedback,
            expand=True,
        )
        paste_style = button_style()
        paste_style.padding = ft.Padding.symmetric(horizontal=16, vertical=6)
        self.paste_button = ft.OutlinedButton(
            self.tr("Paste"),
            icon=ft.Icons.CONTENT_PASTE,
            height=self.text_field.height,
            style=paste_style,
            on_click=self.paste_link,
        )
        self.destination = ft.Text(self.tr("Loading download folder…"), size=12)
        self.folder_note = ft.Text(
            self.tr("Download folder"),
            size=11,
            expand=True,
            color=ft.Colors.ON_SURFACE_VARIANT,
            overflow=ft.TextOverflow.ELLIPSIS,
        )
        self.status_text = ft.Text("", size=13, weight=ft.FontWeight.W_500)
        self.description_text = ft.Text("", size=12, color=ft.Colors.ON_SURFACE_VARIANT)
        self.status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=19)
        self.progress_ring = ft.ProgressRing(
            width=19, height=19, stroke_width=2, visible=False
        )
        self.feedback = ft.Container(
            visible=False,
            padding=ft.Padding.only(top=20),
            border=ft.Border.only(top=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT)),
            content=ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                controls=[
                    self.status_icon,
                    self.progress_ring,
                    ft.Column(
                        expand=True,
                        spacing=5,
                        controls=[self.status_text, self.description_text],
                    ),
                ],
            ),
        )

    def build_form(
        self,
        title,
        subtitle,
        icon,
        card_title,
        card_subtitle,
        sections,
        note=None,
        note_icon=ft.Icons.LOCK_OUTLINE,
    ):
        self.form = soft_card(
            ft.Column(
                spacing=24,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            soft_icon(icon, 40),
                            ft.Column(
                                expand=True,
                                spacing=5,
                                controls=[
                                    ft.Text(
                                        card_title, size=15, weight=ft.FontWeight.W_500
                                    ),
                                    ft.Text(
                                        card_subtitle,
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    *sections,
                    self.feedback,
                ],
            ),
            padding=28,
        )
        body = ft.Column(
            spacing=20,
            controls=[
                ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text(title, size=24, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                ),
                self.form,
            ],
        )
        if note:
            body.controls.append(self.hint(note, note_icon))
        self.toolbar = components.AppBar(self.manager, localizer=self.localizer)
        self.controls = [
            page_shell(
                self.toolbar,
                body,
                self.folder_note,
                ft.Icons.FOLDER_OUTLINED,
                self.go_to_feedback,
                width=664,
                localizer=self.localizer,
            )
        ]

    def link_section(self, label, helper):
        return ft.Column(
            spacing=10,
            controls=[
                ft.Text(label, size=13, weight=ft.FontWeight.W_500),
                ft.Row(spacing=10, controls=[self.text_field, self.paste_button]),
                ft.Text(helper, size=12, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
        )

    def destination_section(self):
        return ft.Row(
            spacing=12,
            controls=[
                ft.Icon(
                    ft.Icons.FOLDER_OUTLINED,
                    size=20,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Column(
                    expand=True,
                    spacing=5,
                    controls=[
                        ft.Text(
                            self.tr("Will be downloaded to"),
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                        self.destination,
                    ],
                ),
            ],
        )

    @staticmethod
    def divider():
        return ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)

    @staticmethod
    def hint(text, icon):
        return ft.Row(
            spacing=8,
            controls=[
                ft.Icon(icon, size=14, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(text, size=12, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
            ],
        )

    def set_busy(self, busy):
        self.busy = busy
        self.text_field.read_only = busy
        self.paste_button.disabled = self.download_button.disabled = busy
        for button in self.date_buttons:
            button.disabled = busy

    def refresh(self):
        if self.active:
            self.update()

    def clear_feedback(self, e=None):
        self.feedback.visible = False
        self.refresh()

    def show_feedback(self, title, detail, error=False, busy=False):
        self.feedback.visible = True
        self.status_text.value = title
        self.description_text.value = detail
        self.status_icon.icon = (
            ft.Icons.ERROR_OUTLINE if error else ft.Icons.CHECK_CIRCLE_OUTLINE
        )
        self.status_icon.color = ft.Colors.ERROR if error else ft.Colors.PRIMARY
        self.status_icon.visible = not busy
        self.progress_ring.visible = busy
        self.refresh()

    async def paste_link(self, e=None):
        try:
            value = await ft.Clipboard().get()
            if value:
                self.text_field.value = value.strip()
                self.clear_feedback()
        except Exception as error:
            logger.exception("Could not read clipboard", exc_info=error)
            self.show_feedback(
                self.tr("Couldn't read the clipboard."),
                self.tr("Paste the link directly into the field."),
                error=True,
            )

    def did_mount(self):
        self.folder_task = asyncio.create_task(self.load_destination())

    def will_unmount(self):
        self.active = False
        for task in (self.folder_task, self.operation_task):
            if task and not task.done():
                task.cancel()

    async def load_destination(self):
        try:
            folder = await get_destination_folder()
        except Exception:
            logger.exception("Could not load download folder")
            folder = None
        label = (
            str(folder) if folder else self.tr("Choose a download folder in Settings")
        )
        home = str(Path.home())
        display = "~" + label[len(home) :] if label.startswith(home + "/") else label
        self.destination.value = self.folder_note.value = display
        self.destination.tooltip = self.folder_note.tooltip = label
        self.refresh()

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")
