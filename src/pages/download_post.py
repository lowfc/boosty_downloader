import asyncio
from urllib.parse import urlparse

import flet as ft

from components.soft_layout import button_style
from core.downloads_manager import DownloadManager
from core.logger import setup_logger
from core.utils import parse_post_link
from pages.post_download_form import PostDownloadForm, author_from_input

logger = setup_logger()


class DownloadPostPage(PostDownloadForm):
    def __init__(self, manager: DownloadManager, localizer=None):
        super().__init__(
            manager,
            "/download-post",
            "https://boosty.to/author/posts/…",
            self.download_post,
            localizer=localizer,
        )
        self.download_button = ft.Button(
            self.tr("Download post"),
            icon=ft.Icons.DOWNLOAD_OUTLINED,
            height=42,
            style=button_style(primary=True),
            on_click=self.download_post,
        )
        self.build_form(
            self.tr("One post"),
            self.tr("Download a specific post by its direct link."),
            ft.Icons.LINK,
            self.tr("Choose a post"),
            self.tr("Copy the post link from Boosty."),
            [
                self.link_section(
                    self.tr("Post link"),
                    self.tr("Use a direct post link, rather than an author's page."),
                ),
                self.divider(),
                self.destination_section(),
                self.hint(
                    self.tr("Uses your content and quality settings."), ft.Icons.TUNE
                ),
                ft.Row(
                    wrap=True,
                    spacing=16,
                    run_spacing=10,
                    controls=[
                        self.download_button,
                        ft.Text(
                            self.tr("Progress appears in Downloads."),
                            size=12,
                            color=ft.Colors.ON_SURFACE_VARIANT,
                        ),
                    ],
                ),
            ],
            note=self.tr("Only content you have access to can be downloaded."),
        )

    async def download_post(self, e=None):
        if self.busy:
            return
        value = (self.text_field.value or "").strip()
        link = parse_post_link(value)
        try:
            url = urlparse(value if "://" in value else f"https://{value}")
        except ValueError:
            url = urlparse("")
        if (
            not link
            or not author_from_input(link.author)
            or url.netloc.lower() != "boosty.to"
            or url.scheme not in ("http", "https")
            or url.path.rstrip("/") != f"/{link.author}/posts/{link.id}"
        ):
            self.show_feedback(
                (
                    self.tr("Paste a post link to continue.")
                    if not value
                    else self.tr("This link doesn't lead to a Boosty post.")
                ),
                self.tr("Copy a direct post link from Boosty and try again."),
                error=True,
            )
            return
        self.operation_task = asyncio.current_task()
        self.set_busy(True)
        self.show_feedback(
            self.tr("Adding post to Downloads…"),
            self.tr("Your download will appear in the queue."),
            busy=True,
        )
        try:
            added = await self.manager.add_task(link.author, link.id)
            self.text_field.value = ""
            if added:
                self.show_feedback(
                    self.tr("Post added to Downloads."),
                    self.tr("You can follow the download progress there."),
                )
            else:
                self.show_feedback(
                    self.tr("This post is already in Downloads."),
                    self.tr("Follow its progress or retry it from Downloads."),
                )
        except Exception as error:
            logger.exception("Could not queue post", exc_info=error)
            self.show_feedback(
                self.tr("Couldn't add this post."),
                self.tr("Please try again."),
                error=True,
            )
        finally:
            self.set_busy(False)
            self.operation_task = None
            self.refresh()
