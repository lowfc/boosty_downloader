import asyncio
from pathlib import Path

import aiofiles
import flet as ft

from components.soft_layout import button_style
from core.boosty.client import BoostyClient
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import get_destination_folder, get_download_settings, parse_image_link
from pages.post_download_form import PostDownloadForm

logger = setup_logger()


class DownloadImageByLinkPage(PostDownloadForm):
    def __init__(self, manager: DownloadManager):
        super().__init__(
            manager,
            "/download-media-by-link",
            "https://boosty.to/author/blog/media/…",
            self.download_image,
        )
        self.destination_path = None
        self.text_field.height = 44
        self.text_field.content_padding = ft.Padding.symmetric(
            horizontal=14, vertical=14
        )
        self.destination_folder_picker = ft.OutlinedButton(
            "Change", style=button_style(), on_click=self.pick_destination_folder
        )
        self.download_button = ft.Button(
            "Download image",
            icon=ft.Icons.DOWNLOAD_OUTLINED,
            height=42,
            style=button_style(primary=True),
            on_click=self.download_image,
        )
        self.progress = ft.ProgressBar(
            color=ft.Colors.PRIMARY, value=None, visible=False, height=5
        )
        self.feedback.content.controls[-1].controls.append(self.progress)
        destination_section = self.destination_section()
        destination_section.controls.append(self.destination_folder_picker)
        self.build_form(
            "Image by link",
            "Download an image from your feed or private messages.",
            ft.Icons.IMAGE_OUTLINED,
            "Choose an image",
            "Copy its direct link from Boosty.",
            [
                self.link_section(
                    "Image link",
                    "Open the image on Boosty and copy the link from your browser.",
                ),
                self.divider(),
                destination_section,
                ft.Row(
                    wrap=True,
                    spacing=16,
                    run_spacing=10,
                    controls=[
                        self.download_button,
                        ft.Text(
                            "Saved as a JPG file.",
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            ],
            note="For a full post with multiple images, use One post.",
            note_icon=ft.Icons.LINK,
        )

    def set_destination(self, folder):
        self.destination_path = Path(folder) if folder else None
        label = str(folder) if folder else "Choose a download folder"
        home = str(Path.home())
        display = "~" + label[len(home) :] if label.startswith(home + "/") else label
        self.destination.value = self.folder_note.value = display
        self.destination.tooltip = self.folder_note.tooltip = label

    async def load_destination(self):
        try:
            folder = await get_destination_folder()
            if not self.active:
                return
            self.set_destination(folder)
            self.refresh()
        except Exception:
            logger.exception("Could not load image download folder")
            self.set_destination(None)
            self.show_feedback(
                "Choose a download folder.",
                "Use Change to select an existing folder.",
                error=True,
            )

    async def pick_destination_folder(self, e=None):
        if self.busy:
            return
        try:
            folder = await ft.FilePicker().get_directory_path()
            if folder and self.active:
                self.set_destination(folder)
                self.clear_feedback()
        except Exception:
            logger.exception("Could not choose image download folder")
            self.show_feedback(
                "Couldn't open the folder picker.",
                "Please try again.",
                error=True,
            )

    def set_busy(self, busy):
        super().set_busy(busy)
        self.destination_folder_picker.disabled = busy

    async def download_image(self, e=None):
        if self.busy:
            return
        link = (self.text_field.value or "").strip()
        link_uuid = parse_image_link(link)
        if not link_uuid:
            self.show_feedback(
                "Check the image link.",
                "Use a direct Boosty image link from your feed or messages.",
                error=True,
            )
            return
        if not self.destination_path or not self.destination_path.is_dir():
            self.show_feedback(
                "Choose an existing download folder.",
                "Use Change to select the folder where the image will be saved.",
                error=True,
            )
            return
        download_path = self.destination_path / f"{link_uuid}.jpg"
        if download_path.exists():
            self.show_feedback(
                "This image is already saved.", str(download_path), error=True
            )
            return
        self.operation_task = asyncio.current_task()
        self.set_busy(True)
        self.progress.visible = True
        self.progress.value = None
        self.show_feedback("Downloading image…", str(download_path.parent), busy=True)
        created_file = completed = False
        try:
            settings = await get_download_settings()
            if not settings:
                raise ValueError("Download settings unavailable")
            client = BoostyClient(
                chunk_size=settings.chunk_size,
                download_timeout=settings.download_timeout,
            )
            async with (
                client.get_client_session() as session,
                session.get(f"https://images.boosty.to/image/{link_uuid}") as response,
            ):
                response.raise_for_status()
                total = response.content_length
                downloaded = 0
                async with aiofiles.open(download_path, "xb") as target:
                    created_file = True
                    async for chunk in response.content.iter_chunked(
                        settings.chunk_size
                    ):
                        await target.write(chunk)
                        downloaded += len(chunk)
                        self.progress.value = (
                            min(1, downloaded / total) if total else None
                        )
                        self.refresh()
            completed = True
            self.show_feedback("Image saved.", str(download_path))
        except FileExistsError:
            self.show_feedback(
                "This image is already saved.", str(download_path), error=True
            )
        except Exception:
            logger.exception("Failed to download image")
            self.show_feedback(
                "Couldn't download the image.",
                "Check your connection and folder permissions, then try again.",
                error=True,
            )
        finally:
            if created_file and not completed:
                try:
                    download_path.unlink(missing_ok=True)
                except OSError:
                    logger.exception("Could not remove incomplete image")
            self.set_busy(False)
            self.progress.visible = False
            self.progress.value = None
            self.progress_ring.visible = False
            self.operation_task = None
            self.refresh()
