import asyncio
from pathlib import Path

import aiofiles
import flet as ft

import components
from core.boosty.client import BoostyClient
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.progress_counter import ProgressCounter
from core.utils import parse_image_link, get_download_settings

logger = setup_logger()


class DownloadImageByLinkPage(ft.View):
    def __init__(self, manager: DownloadManager):
        super().__init__()
        self.route = "/download-media-by-link"
        self.destination_folder_valid = False
        self.current_destination_folder_text = ft.Text(
            value="Choose download folder",
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
                        self.current_destination_folder_text,
                    ],
                ),
            ),
            on_click=self.pick_destination_folder,
        )
        self.text_field = ft.TextField(
            prefix_icon=ft.IconButton(ft.Icons.LINK, on_click=self.download_image),
            hint_text="https://boosty.to/author/blog/media/053713d9-93df-4f4a-ae45-e01ea031cb15/9b981067-9854-4af0-aed4-6b5efe3ad96f",
            width=500,
            value="",
            border_color=ft.Colors.TRANSPARENT,
            filled=True,
            fill_color=ft.Colors.SURFACE_CONTAINER,
            hint_style=ft.TextStyle(color=ft.Colors.GREY_600),
        )
        self.progress = ft.ProgressBar(
            color=ft.Colors.ORANGE, width=500, value=0, visible=False
        )
        self.controls = [
            components.AppBar(manager),
            ft.Row(
                controls=[
                    ft.IconButton(
                        ft.Icon(ft.Icons.ARROW_BACK), on_click=self.go_to_index
                    ),
                    ft.Text(
                        "Download image by link", size=24, weight=ft.FontWeight.BOLD
                    ),
                ]
            ),
            ft.Row(
                [
                    ft.Column(
                        [
                            self.progress,
                            ft.Text(
                                "Paste here link to the image (from feed or direct messages)"
                            ),
                            self.text_field,
                            self.destination_folder_picker,
                            ft.Button(
                                content=ft.Text("Download", size=17),
                                icon=ft.Icon(
                                    ft.Icons.DOWNLOAD, color=ft.Colors.PRIMARY, size=16
                                ),
                                height=50,
                                width=150,
                                color=ft.Colors.ON_SURFACE,
                                on_click=self.download_image,
                            ),
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
        asyncio.create_task(self.async_build())

    async def async_build(self):
        default_downloads_path = Path().home() / "Downloads"
        if default_downloads_path:
            self.current_destination_folder_text.value = str(default_downloads_path)
        else:
            self.current_destination_folder_text.value = ""
        self.page.update()

    async def pick_destination_folder(self):
        path = await ft.FilePicker().get_directory_path()
        if not path:
            return
        self.current_destination_folder_text.value = path
        self.page.update()

    async def download_image(self):
        link = self.text_field.value.strip()
        if not link:
            if clipboard := await ft.Clipboard().get():
                link = clipboard.strip()
        if not link:
            return

        link_uuid = parse_image_link(link)
        if not link_uuid:
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Not this link"),
                    content=ft.Text(
                        "This utility is for download a PICTURE using a direct link (to picture) from "
                        "the posts list or private messages (you can get this link in the browser address bar)."
                    ),
                    actions=[
                        ft.TextButton(
                            "I get it", on_click=lambda ev: self.page.pop_dialog()
                        )
                    ],
                    open=True,
                )
            )
            return
        base_path = Path(self.current_destination_folder_text.value)
        if not base_path.exists():
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Folder does not exist"),
                    content=ft.Text("Download folder does not exist"),
                    actions=[
                        ft.TextButton(
                            "Ok, i'll create",
                            on_click=lambda ev: self.page.pop_dialog(),
                        )
                    ],
                    open=True,
                )
            )
            return
        download_path = base_path / f"{link_uuid}.jpg"
        if download_path.exists():
            self.page.show_dialog(
                ft.AlertDialog(
                    title=ft.Text("Already exists"),
                    content=ft.Text("File with this name already exists"),
                    actions=[
                        ft.TextButton(
                            "Understood", on_click=lambda e: self.page.pop_dialog()
                        )
                    ],
                    open=True,
                )
            )
            return

        self.disabled = True
        self.progress.visible = True
        self.page.update()
        await asyncio.sleep(0.1)

        settings = await get_download_settings()
        client = BoostyClient(
            chunk_size=settings.chunk_size,
            download_timeout=settings.download_timeout,
        )

        try:
            with ProgressCounter(total=0) as pbar:
                session = client.get_client_session()
                async with session:
                    async with session.get(
                        f"https://images.boosty.to/image/{link_uuid}"
                    ) as response:
                        response.raise_for_status()
                        pbar.total = response.content_length
                        async with aiofiles.open(download_path, "wb") as f:
                            async for chunk in response.content.iter_chunked(
                                settings.chunk_size
                            ):
                                if not chunk:
                                    continue
                                await f.write(chunk)
                                chunk_size = len(chunk)
                                pbar.update(chunk_size)
                                total = pbar.total or chunk_size
                                self.progress.value = pbar.n / total
                                self.progress.update()
            self.page.show_dialog(ft.SnackBar(ft.Text("Saved")))
        except Exception as e:
            logger.error("Failed to download image", exc_info=e)
        finally:
            self.text_field.value = ""
            self.disabled = False
            self.progress.visible = False
            self.progress.value = 0
            self.page.update()
