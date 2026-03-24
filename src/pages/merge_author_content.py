import asyncio
import os
import shutil
from pathlib import Path

import flet as ft

import components
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_download_settings

logger = setup_logger()


class MergeAuthorContentPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/merge-author-content"
        self.settings = None
        self.destination_folder_valid = False
        self.action_type = ft.Dropdown(
            width=500,
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            label="Action",
            value="copy",
            options=[
                ft.DropdownOption(key="copy", text="Copy"),
                ft.DropdownOption(key="move", text="Move"),
            ],
        )
        self.authors_dropdown = ft.Dropdown(
            width=500,
            label="Choose author's folder",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            on_select=self.update_state,
        )
        self.current_merge_folder_text = ft.Text(
            value="Choose destination folder",
            size=20,
            color=ft.Colors.ON_SURFACE_VARIANT,
            width=430,
            overflow=ft.TextOverflow.ELLIPSIS,
            max_lines=1,
        )
        self.destination_folder_picker = ft.Button(
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=5)),
            width=500,
            content=ft.Container(
                height=50,
                padding=ft.Padding.all(5),
                content=ft.Row(
                    spacing=10,
                    controls=[
                        ft.Icon(
                            ft.Icons.FOLDER, size=20, color=ft.Colors.ON_SURFACE_VARIANT
                        ),
                        self.current_merge_folder_text,
                    ],
                ),
            ),
            on_click=self.pick_destination_folder,
        )
        self.merge_photos_check = ft.Checkbox(
            label="Photos", value=False, on_change=self.update_state
        )
        self.merge_videos_check = ft.Checkbox(
            label="Videos", value=False, on_change=self.update_state
        )
        self.merge_audios_check = ft.Checkbox(
            label="Audios", value=False, on_change=self.update_state
        )
        self.add_post_title_to_filename = ft.Checkbox(
            label="Add post title to filename", value=False, width=200
        )
        self.proceed_button = ft.Button(
            "Proceed", width=200, height=50, disabled=True, on_click=self.do_merge
        )
        self.controls = [
            components.AppBar(manager),
            ft.Row(
                [
                    ft.IconButton(
                        ft.Icon(ft.Icons.ARROW_BACK), on_click=self.go_to_index
                    ),
                    ft.Text("Content merger", size=24, weight=ft.FontWeight.BOLD),
                ]
            ),
            ft.ListView(
                [
                    ft.Column(
                        [
                            ft.Text(
                                "Transfer content from the author's post folders to one folder"
                            ),
                            self.action_type,
                            ft.Icon(ft.Icons.ARROW_DOWNWARD),
                            self.authors_dropdown,
                            ft.Icon(ft.Icons.ARROW_DOWNWARD),
                            self.destination_folder_picker,
                            ft.Row(
                                [
                                    self.merge_photos_check,
                                    self.merge_videos_check,
                                    self.merge_audios_check,
                                ],
                                spacing=15,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            self.add_post_title_to_filename,
                            self.proceed_button,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        expand=True,
                        spacing=20,
                    )
                ],
                expand=True,
            ),
        ]

    async def go_to_index(self):
        await self.page.push_route("/")

    def build(self):
        asyncio.create_task(self.load_main_options())

    async def load_main_options(self):
        self.settings = await get_download_settings()
        folders = []
        folder = Path(self.settings.downloads_folder)
        if folder.exists():
            folders = [d.name for d in folder.iterdir() if d.is_dir()]
        self.authors_dropdown.options = [
            ft.DropdownOption(key=str(i), text=str(i)) for i in folders
        ]
        self.page.update()

    async def update_state(self):
        self.proceed_button.disabled = not (
            self.destination_folder_valid
            and self.authors_dropdown.value
            and any(
                (
                    self.merge_photos_check.value,
                    self.merge_videos_check.value,
                    self.merge_audios_check.value,
                )
            )
        )
        self.page.update()

    async def pick_destination_folder(self):
        path = await ft.FilePicker().get_directory_path()
        if path and self.settings and self.settings.downloads_folder != path:
            self.current_merge_folder_text.value = path
            self.destination_folder_valid = True
            await self.update_state()

    async def do_merge(self):
        source_folder = (
            Path(self.settings.downloads_folder) / self.authors_dropdown.value
        )
        destination_folder = Path(self.current_merge_folder_text.value)
        if not source_folder.exists() or not destination_folder.exists():
            return
        self.disabled = True
        self.proceed_button.text = "Working..."
        self.page.update()
        await asyncio.sleep(2)
        posts = os.listdir(source_folder)
        stats = {
            "posts": 0,
            "photos": 0,
            "videos": 0,
            "audios": 0,
        }
        need_photos = self.merge_photos_check.value
        need_videos = self.merge_videos_check.value
        need_audios = self.merge_audios_check.value
        photo_extensions = {
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
        video_extensions = {
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
        audio_extensions = {
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".ogg",
            ".wma",
            ".m4a",
            ".aiff",
        }
        action = self.action_type.value
        add_post_filename = self.add_post_title_to_filename.value
        for post in posts:
            if post == ".DS_Store":
                continue
            post_directory = source_folder / post
            if not os.path.isdir(post_directory):
                continue
            stats["posts"] += 1
            for filename in os.listdir(post_directory):
                source_path = source_folder / post / filename
                if not os.path.isfile(source_path):
                    continue
                file_ext = source_path.suffix.lower()

                file_type = None
                if need_photos and file_ext in photo_extensions:
                    file_type = "photos"
                elif need_videos and file_ext in video_extensions:
                    file_type = "videos"
                elif need_audios and file_ext in audio_extensions:
                    file_type = "audios"

                if not file_type:
                    continue

                if add_post_filename:
                    target_path = destination_folder / (post + "_" + filename)
                else:
                    target_path = destination_folder / filename
                if target_path.exists():
                    continue

                try:
                    if action == "copy":
                        logger.info(f"Copying {source_path} to {target_path}")
                        shutil.copy(source_path, target_path)
                    else:
                        logger.info(f"Moving {source_path} to {target_path}")
                        shutil.move(source_path, target_path)
                    stats[file_type] += 1
                except Exception as e:
                    logger.error("Error on moving file", exc_info=e)
        text_result = "Copied" if action == "copy" else "Moved"
        text_result += f" {stats['photos']} photos, {stats['videos']} videos, {stats['audios']} audios from {stats['posts']} posts."
        self.page.show_dialog(
            ft.AlertDialog(
                title=ft.Text("Done"),
                content=ft.Text(text_result),
                actions=[ft.TextButton("Ok", on_click=self.page.pop_dialog)],
                open=True,
            )
        )
        self.disabled = False
        self.proceed_button.text = "Proceed"
        self.page.update()
