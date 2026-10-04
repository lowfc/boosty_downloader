import asyncio
import shutil
from pathlib import Path

import flet as ft

import __version__ as app_version
import components
from components.soft_layout import button_style, page_shell, soft_card, soft_icon
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_download_settings
from localization import Localizer

logger = setup_logger()

PHOTO_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".tiff",
    ".webp",
    ".heic",
    ".raw",
}
VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mpg",
    ".mpeg",
}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".aiff"}


class MergeAuthorContentPage(ft.View):
    def __init__(self, manager: DownloadManager, localizer=None):
        super().__init__()
        self.localizer = localizer or Localizer()
        self.tr = self.localizer.t
        self.route = "/merge-author-content"
        self.padding = self.spacing = 0
        self.active = True
        self.busy = False
        self.settings = None
        self.load_task = self.operation_task = None
        self.destination_path = None
        self.action_type = "copy"
        self.authors_dropdown = ft.Dropdown(
            expand=True,
            text_size=13,
            dense=True,
            filled=True,
            fill_color=ft.Colors.SURFACE,
            hint_text=self.tr("Choose an author"),
            disabled=True,
            border=ft.OutlineInputBorder(
                side=ft.BorderSide(1, ft.Colors.OUTLINE_VARIANT), border_radius=9
            ),
            on_select=self.update_state,
        )
        self.source_help = ft.Text(
            self.tr("Loading author folders…"),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.action_help = ft.Text(
            self.tr("Keep files in their original post folders."),
            size=12,
            color=ft.Colors.ON_SURFACE_VARIANT,
        )
        self.action_buttons = {
            "copy": ft.OutlinedButton(
                self.tr("Copy"),
                icon=ft.Icon(ft.Icons.COPY_OUTLINED, size=16),
                expand=True,
                height=36,
                on_click=lambda e: self.select_action("copy"),
            ),
            "move": ft.OutlinedButton(
                self.tr("Move"),
                icon=ft.Icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED, size=16),
                expand=True,
                height=36,
                on_click=lambda e: self.select_action("move"),
            ),
        }
        self.action_selector = ft.Container(
            padding=3,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            border_radius=9,
            bgcolor=ft.Colors.SURFACE,
            content=ft.Row(list(self.action_buttons.values()), spacing=0),
        )
        self.current_merge_folder_text = ft.Text(
            self.tr("Choose a destination folder"), size=13
        )
        self.destination_folder_picker = ft.OutlinedButton(
            self.tr("Change"),
            style=button_style(),
            on_click=self.pick_destination_folder,
        )
        self.merge_photos_check = ft.Checkbox(
            label=self.tr("Photos"),
            value=True,
            label_style=ft.TextStyle(size=13),
            on_change=self.update_state,
        )
        self.merge_videos_check = ft.Checkbox(
            label=self.tr("Videos"),
            value=True,
            label_style=ft.TextStyle(size=13),
            on_change=self.update_state,
        )
        self.merge_audios_check = ft.Checkbox(
            label=self.tr("Audio"),
            value=False,
            label_style=ft.TextStyle(size=13),
            on_change=self.update_state,
        )
        self.content_tiles = [
            self.content_tile(self.merge_photos_check, ft.Icons.IMAGE_OUTLINED),
            self.content_tile(self.merge_videos_check, ft.Icons.VIDEOCAM_OUTLINED),
            self.content_tile(self.merge_audios_check, ft.Icons.MUSIC_NOTE_OUTLINED),
        ]
        self.add_post_title_to_filename = ft.Checkbox(
            label=self.tr("Add post title to filenames"),
            value=False,
            label_style=ft.TextStyle(size=13),
            on_change=self.update_state,
        )
        self.proceed_button = ft.Button(
            self.tr("Copy content"),
            icon=ft.Icons.DRIVE_FILE_MOVE_OUTLINED,
            height=42,
            style=button_style(primary=True),
            disabled=True,
            on_click=self.do_merge,
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
                        [self.status_text, self.description_text],
                        spacing=5,
                        expand=True,
                    ),
                ],
            ),
        )
        self.form = soft_card(
            ft.Column(
                spacing=24,
                controls=[
                    ft.Row(
                        spacing=14,
                        controls=[
                            soft_icon(ft.Icons.DRIVE_FILE_MOVE_OUTLINED, 40),
                            ft.Column(
                                expand=True,
                                spacing=5,
                                controls=[
                                    ft.Text(
                                        self.tr("Organize your files"),
                                        size=15,
                                        weight=ft.FontWeight.W_500,
                                    ),
                                    ft.Text(
                                        self.tr(
                                            "Choose a source, a destination and the content to include."
                                        ),
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.ResponsiveRow(
                        spacing=22,
                        run_spacing=22,
                        controls=[
                            ft.Column(
                                col={"xs": 12, "sm": 6},
                                spacing=10,
                                controls=[
                                    self.label(self.tr("Author folder")),
                                    ft.Row([self.authors_dropdown]),
                                    self.source_help,
                                ],
                            ),
                            ft.Column(
                                col={"xs": 12, "sm": 6},
                                spacing=10,
                                controls=[
                                    self.label(self.tr("Action")),
                                    self.action_selector,
                                    self.action_help,
                                ],
                            ),
                        ],
                    ),
                    self.divider(),
                    ft.Row(
                        spacing=14,
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
                                        self.tr("Destination folder"),
                                        size=12,
                                        color=ft.Colors.ON_SURFACE_VARIANT,
                                    ),
                                    self.current_merge_folder_text,
                                ],
                            ),
                            self.destination_folder_picker,
                        ],
                    ),
                    self.divider(),
                    ft.Column(
                        spacing=14,
                        controls=[
                            self.label(self.tr("Content to include")),
                            ft.ResponsiveRow(
                                self.content_tiles, spacing=10, run_spacing=10
                            ),
                            self.add_post_title_to_filename,
                            ft.Text(
                                self.tr(
                                    "Existing files in the destination folder are skipped."
                                ),
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                    ft.Row(
                        spacing=16,
                        run_spacing=10,
                        wrap=True,
                        controls=[
                            self.proceed_button,
                            ft.Text(
                                self.tr("Works with files already downloaded."),
                                size=12,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            ),
                        ],
                    ),
                    self.feedback,
                ],
            ),
            padding=28,
        )
        self.toolbar = components.AppBar(manager, localizer=self.localizer)
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
                                    self.tr("Merge content"),
                                    size=24,
                                    weight=ft.FontWeight.W_500,
                                ),
                                ft.Text(
                                    self.tr(
                                        "Collect an author's downloaded files in one folder."
                                    ),
                                    size=13,
                                    color=ft.Colors.ON_SURFACE_VARIANT,
                                ),
                            ],
                        ),
                        self.form,
                    ],
                ),
                ft.Text(
                    f"{app_version.NAME} · {app_version.VERSION}",
                    size=11,
                    expand=True,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Icons.INFO_OUTLINE,
                self.go_to_feedback,
                width=688,
                localizer=self.localizer,
            )
        ]
        self.update_state(refresh=False)

    @staticmethod
    def label(text):
        return ft.Text(text, size=13, weight=ft.FontWeight.W_500)

    @staticmethod
    def divider():
        return ft.Divider(height=1, color=ft.Colors.OUTLINE_VARIANT)

    @staticmethod
    def content_tile(checkbox, icon):
        checkbox.expand = True
        return ft.Container(
            col={"xs": 12, "sm": 4},
            padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            border_radius=10,
            border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            content=ft.Row([ft.Icon(icon, size=17), checkbox], spacing=2),
        )

    def refresh(self):
        if self.active:
            self.update()

    def did_mount(self):
        self.load_task = asyncio.create_task(self.load_main_options())

    def will_unmount(self):
        self.active = False
        if self.load_task and not self.load_task.done():
            self.load_task.cancel()
        # An in-flight file transfer finishes; no new transfers start after leaving.

    async def load_main_options(self):
        try:
            self.settings = await get_download_settings()
            if not self.settings:
                raise ValueError(self.tr("Download folder unavailable"))
            folder = Path(self.settings.downloads_folder)
            folders = await asyncio.to_thread(
                lambda: (
                    sorted(d.name for d in folder.iterdir() if d.is_dir())
                    if folder.is_dir()
                    else []
                )
            )
            if not self.active:
                return
            self.authors_dropdown.options = [
                ft.DropdownOption(key=name, text=name) for name in folders
            ]
            self.authors_dropdown.disabled = not folders
            self.update_state()
        except Exception:
            logger.exception("Could not load author folders")
            self.source_help.value = self.tr("Author folders unavailable.")
            self.show_feedback(
                self.tr("Couldn't load author folders."),
                self.tr(
                    "Check your download folder in Settings, then reopen this page."
                ),
                error=True,
            )

    def select_action(self, action):
        if not self.busy and action in self.action_buttons:
            self.action_type = action
            self.update_state()

    def update_state(self, e=None, refresh=True):
        self.feedback.visible = False
        selected_author = self.authors_dropdown.value
        if self.settings and selected_author:
            path = Path(self.settings.downloads_folder) / selected_author
            self.source_help.value = self.display_path(path)
            self.source_help.tooltip = str(path)
        elif self.settings:
            self.source_help.value = (
                self.tr("Choose an author's downloaded folder.")
                if self.authors_dropdown.options
                else self.tr("No downloaded authors found. Download a post first.")
            )
        for key, button in self.action_buttons.items():
            selected = key == self.action_type
            button.style = ft.ButtonStyle(
                color=(
                    ft.Colors.ON_SURFACE if selected else ft.Colors.ON_SURFACE_VARIANT
                ),
                bgcolor=(
                    ft.Colors.SURFACE_CONTAINER_LOWEST
                    if selected
                    else ft.Colors.TRANSPARENT
                ),
                side=ft.BorderSide(1 if selected else 0, ft.Colors.OUTLINE_VARIANT),
                shape=ft.RoundedRectangleBorder(radius=7),
                padding=ft.Padding.symmetric(horizontal=10, vertical=6),
                text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
            )
        self.action_help.value = (
            self.tr("Keep files in their original post folders.")
            if self.action_type == "copy"
            else self.tr("Transfer files out of their original post folders.")
        )
        self.proceed_button.content = (
            self.tr("Copy content")
            if self.action_type == "copy"
            else self.tr("Move content")
        )
        self.proceed_button.disabled = self.busy or not (
            self.settings
            and selected_author
            and self.destination_path
            and any(
                check.value
                for check in (
                    self.merge_photos_check,
                    self.merge_videos_check,
                    self.merge_audios_check,
                )
            )
        )
        for tile, checkbox in zip(
            self.content_tiles,
            (self.merge_photos_check, self.merge_videos_check, self.merge_audios_check),
        ):
            tile.bgcolor = (
                ft.Colors.PRIMARY_CONTAINER if checkbox.value else ft.Colors.SURFACE
            )
            tile.content.controls[0].color = (
                ft.Colors.PRIMARY if checkbox.value else ft.Colors.ON_SURFACE_VARIANT
            )
        if refresh:
            self.refresh()

    @staticmethod
    def display_path(path):
        label, home = str(path), str(Path.home())
        return "~" + label[len(home) :] if label.startswith(home + "/") else label

    async def pick_destination_folder(self, e=None):
        if self.busy:
            return
        try:
            path = await ft.FilePicker().get_directory_path()
            if not path or not self.active:
                return
            destination = Path(path)
            if not destination.is_dir() or (
                self.settings
                and destination.resolve()
                == Path(self.settings.downloads_folder).resolve()
            ):
                self.show_feedback(
                    self.tr("Choose a different destination folder."),
                    self.tr(
                        "Select an existing folder other than the main download folder."
                    ),
                    error=True,
                )
                return
            self.destination_path = destination
            self.current_merge_folder_text.value = self.display_path(destination)
            self.current_merge_folder_text.tooltip = str(destination)
            self.update_state()
        except Exception:
            logger.exception("Could not choose merge destination")
            self.show_feedback(
                self.tr("Couldn't open the folder picker."),
                self.tr("Please try again."),
                error=True,
            )

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

    async def do_merge(self, e=None):
        if self.busy:
            return
        selected = {
            key: extensions
            for key, extensions, checkbox in (
                ("photos", PHOTO_EXTENSIONS, self.merge_photos_check),
                ("videos", VIDEO_EXTENSIONS, self.merge_videos_check),
                ("audios", AUDIO_EXTENSIONS, self.merge_audios_check),
            )
            if checkbox.value
        }
        author = self.authors_dropdown.value
        if not self.settings or not author or not selected or not self.destination_path:
            self.show_feedback(
                self.tr("Choose a source, destination and content."),
                self.tr(
                    "Select an author folder, a destination and at least one content type."
                ),
                error=True,
            )
            return
        source = Path(self.settings.downloads_folder) / author
        destination = self.destination_path
        if not source.is_dir() or not destination.is_dir():
            self.show_feedback(
                self.tr("A selected folder is unavailable."),
                self.tr("Check the source and destination folders, then try again."),
                error=True,
            )
            return
        action = self.action_type
        add_title = self.add_post_title_to_filename.value
        stats = {
            "posts": 0,
            "photos": 0,
            "videos": 0,
            "audios": 0,
            "skipped": 0,
            "failed": 0,
        }
        self.operation_task = asyncio.current_task()
        self.busy = self.form.disabled = True
        self.show_feedback(
            self.tr("Copying files…") if action == "copy" else self.tr("Moving files…"),
            str(destination),
            busy=True,
        )
        try:
            posts = await asyncio.to_thread(lambda: sorted(source.iterdir()))
            for post in posts:
                if not self.active:
                    break
                if not post.is_dir():
                    continue
                stats["posts"] += 1
                files = await asyncio.to_thread(
                    lambda post=post: sorted(post.iterdir())
                )
                for file in files:
                    if not self.active:
                        break
                    if not file.is_file():
                        continue
                    kind = next(
                        (
                            key
                            for key, extensions in selected.items()
                            if file.suffix.lower() in extensions
                        ),
                        None,
                    )
                    if not kind:
                        continue
                    target = destination / (
                        f"{post.name}_{file.name}" if add_title else file.name
                    )
                    if target.exists():
                        stats["skipped"] += 1
                        continue
                    try:
                        await asyncio.to_thread(
                            shutil.copy if action == "copy" else shutil.move,
                            file,
                            target,
                        )
                        stats[kind] += 1
                    except OSError:
                        stats["failed"] += 1
                        logger.exception("Could not transfer file: %s", file)
            detail = self.tr(
                (
                    "Copied {photos} photos, {videos} videos and {audios} audio files from {posts} post folders."
                    if action == "copy"
                    else "Moved {photos} photos, {videos} videos and {audios} audio files from {posts} post folders."
                ),
                **stats,
            )
            if stats["skipped"]:
                detail += self.tr(
                    " Skipped {count} existing files.", count=stats["skipped"]
                )
            if stats["failed"]:
                detail += self.tr(
                    " {count} files could not be transferred.", count=stats["failed"]
                )
            self.show_feedback(
                (
                    self.tr("Some files couldn't be transferred.")
                    if stats["failed"]
                    else (
                        self.tr("Content copied.")
                        if action == "copy"
                        else self.tr("Content moved.")
                    )
                ),
                detail,
                error=bool(stats["failed"]),
            )
        except Exception:
            logger.exception("Could not merge content")
            self.show_feedback(
                self.tr("Couldn't finish merging content."),
                self.tr(
                    "Check the folders and their permissions, then try again. Files already transferred are preserved."
                ),
                error=True,
            )
        finally:
            self.busy = self.form.disabled = False
            self.progress_ring.visible = False
            self.operation_task = None
            self.refresh()

    async def go_to_feedback(self, e=None):
        await self.page.push_route("/feedback-and-bugs")
