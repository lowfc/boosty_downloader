import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import aiofiles
from aiohttp import ClientSession

from core.authorization_provider import AuthorizationProvider
from core.boosty.client import BoostyClient
from core.boosty.defs import (
    BoostyImageDto,
    BoostyAudioDto,
    BoostyFileDto,
    BoostyVideoDto,
    VIDEO_QUALITY_GRADE,
    BoostyPostDto,
)
from core.defs.common import DownloadingSettingsDto
from core.defs.tasks import TaskError
from core.draftjs_converter import DraftJsConverter
from core.logger import setup_logger
from core.progress_counter import ProgressCounter
from core.utils import validate_windows_dir_name, sign_url, get_download_settings

logger = setup_logger()


@dataclass
class FinalDownloadTaskDto:
    final_url: str
    save_path: Path


class Task:
    """Репрезентация таска фоновой загрузки файлов"""

    def __init__(
        self,
        semaphore: asyncio.Semaphore,
        author: str,
        post_id: str,
        post_info: Optional[BoostyPostDto] = None,
    ):
        self._semaphore = semaphore
        self.author = author
        self.post_id = post_id
        self.title = None
        self.path = None
        self._percent = 0
        self._downloaded_bytes = 0
        self._done = False
        self._pending = False
        self._error = False
        self._task = None
        self._finished = False
        self._count_files = 0
        self._total_weight = 0
        self._post_info = post_info
        self.error_description: Optional[TaskError] = None
        self._built_client: Optional[BoostyClient] = None

    def ready(self) -> bool:
        return not self._done and not self._pending and not self._error

    @property
    def percent(self) -> float:
        return self._percent / 100

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def pending(self) -> bool:
        return self._pending

    @property
    def total_weight(self) -> int:
        return self._total_weight

    @property
    def count_files(self) -> int:
        return self._count_files

    def launch(self):
        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def _build_client(self, force: bool = False) -> Optional[BoostyClient]:
        if not self._built_client or force:
            settings = await get_download_settings()
            if not settings:
                logger.error(
                    "Failed get application settings. It may be that the home folder could not be found."
                )
                return None
            auth_token = await AuthorizationProvider.get_authorization_if_valid()
            self._built_client = BoostyClient(
                chunk_size=settings.chunk_size,
                download_timeout=settings.download_timeout,
                auth_token=auth_token,
            )
        return self._built_client

    async def fetch_file_size(self, url: str) -> Optional[int]:
        client = await self._build_client()
        if not client:
            return None
        session = client.get_client_session()
        logger.info(f"Fetching file size for {url}")
        try:
            async with session.head(url) as response:
                logger.debug(f"Got response {response.status}")
                response.raise_for_status()
                return response.content_length
        except Exception as e:
            logger.error("Failed to fetch file size", exc_info=e)
            return None
        finally:
            await session.close()

    async def stop(self):
        if self._task:
            self._task.cancel()
        self._task = None
        self._pending = False
        self._error = True
        self._finished = True
        self.error_description = TaskError.CANCELLED

    async def retry(self):
        if self._done or self._pending:
            return
        self._percent = 0
        self._error = False
        self.error_description = None
        self._finished = False
        self._task = None
        self._total_weight = 0
        self._count_files = 0
        self.launch()

    async def _download_file(
        self,
        session: ClientSession,
        file_url: str,
        save_path: Path,
        pbar: ProgressCounter,
        chunk_size: int = 153600,
    ):
        if save_path.exists():
            logger.info(f"Skip downloading file {save_path} (already exists)")
            await session.close()
            size = save_path.stat().st_size
            self._downloaded_bytes += size
            pbar.update(size)
            total = pbar.total or 1
            self._percent = (pbar.n / total) * 100
            return
        async with session:
            logger.info(f"Downloading file {file_url}")
            async with session.get(file_url) as response:
                logger.debug(f"Got response {response.status}")
                response.raise_for_status()
                async with aiofiles.open(save_path, "wb") as f:
                    logger.debug(f"Writing file {save_path}")
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if not chunk:
                            continue
                        await f.write(chunk)
                        new_chunk_size = len(chunk)
                        self._downloaded_bytes += new_chunk_size
                        pbar.update(new_chunk_size)
                        total = pbar.total or 1
                        self._percent = (pbar.n / total) * 100

    def _fallback(self, err: TaskError) -> None:
        self._error = True
        self.error_description = err
        self._finished = True
        self._pending = False

    async def _prepare_download_tasks(
        self,
        post_path: Path,
        post_info: BoostyPostDto,
        settings: DownloadingSettingsDto,
    ) -> List[FinalDownloadTaskDto]:
        download_items = []
        for media in post_info.media:
            if (
                isinstance(media, BoostyImageDto) and settings.need_download_photos
            ):  # photo
                self._total_weight += media.size
                download_items.append(
                    FinalDownloadTaskDto(
                        final_url=media.url,
                        save_path=post_path / (media.id + ".jpg"),
                    )
                )

            elif (
                isinstance(media, BoostyVideoDto) and settings.need_download_videos
            ):  # video
                lborder_quality = VIDEO_QUALITY_GRADE.index(
                    settings.preferred_video_size
                )
                for i in range(lborder_quality, len(VIDEO_QUALITY_GRADE)):
                    url_info = media.player_urls.get(VIDEO_QUALITY_GRADE[i])
                    if url_info:
                        file_size = await self.fetch_file_size(url_info.url)
                        if not file_size:
                            raise ValueError(f"Failed fetch file size for {url_info.url}")
                        self._total_weight += file_size
                        path = post_path / validate_windows_dir_name(media.get_title())
                        download_items.append(
                            FinalDownloadTaskDto(
                                final_url=url_info.url,
                                save_path=path,
                            )
                        )
                        break

            elif (
                isinstance(media, BoostyAudioDto) and settings.need_download_audios
            ):  # audio
                if post_info.signed_query:
                    self._total_weight += media.size
                    path = post_path / validate_windows_dir_name(media.get_title())
                    download_items.append(
                        FinalDownloadTaskDto(
                            final_url=sign_url(media.url, post_info.signed_query),
                            save_path=path,
                        )
                    )

            elif (
                isinstance(media, BoostyFileDto) and settings.need_download_files
            ):  # file
                if post_info.signed_query:
                    self._total_weight += media.size
                    path = post_path / validate_windows_dir_name(media.title)
                    download_items.append(
                        FinalDownloadTaskDto(
                            final_url=sign_url(media.url, post_info.signed_query),
                            save_path=path,
                        )
                    )

        return download_items

    async def _run(self):
        if self._done or self._pending:
            return None

        self._pending = True
        async with self._semaphore:
            settings = await get_download_settings()
            if not settings:
                logger.error(
                    "Failed get application settings. It may be that the home folder could not be found."
                )
                return self._fallback(TaskError.ERROR)
            client = await self._build_client(force=True)
            if not client:
                logger.error(
                    "Failed build client, task skipped"
                )
                return self._fallback(TaskError.ERROR)

            if self._post_info:
                post_info = self._post_info
            else:
                try:
                    post_info = await client.get_post_info(self.author, self.post_id)
                except Exception as e:
                    logger.error(
                        "Failed fetch post info due unexpected error", exc_info=e
                    )
                    return self._fallback(TaskError.ERROR)

            if post_info.title:
                self.title = post_info.title

            if not post_info.has_access:
                logger.error(
                    f"User have no access to the post {self.post_id}, cancelled"
                )
                return self._fallback(TaskError.ACCESS_DENIED)

            downloads_folder = Path(settings.downloads_folder)
            logger.info(f"Home dir: {downloads_folder}")

            try:
                if not os.path.isdir(settings.downloads_folder):
                    logger.error(
                        f"Home directory does not exist: {settings.downloads_folder}, creating..."
                    )
                    downloads_folder.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed create or check home directory", exc_info=e)
                return self._fallback(TaskError.NO_HOME_FOLDER)

            post_path = Path(settings.downloads_folder) / self.author / self.post_id
            if post_info.title:
                if title := validate_windows_dir_name(post_info.title):
                    post_path = (
                        Path(settings.downloads_folder)
                        / self.author
                        / (title + "_" + self.post_id)
                    )

            self.path = post_path
            if not os.path.isdir(post_path):
                post_path.mkdir(parents=True)
                logger.info(f"Post directory created: {post_path}")

            try:
                parser = DraftJsConverter(post_info.text_content.content)
                post_time = datetime.fromtimestamp(post_info.publish_time)
                fmt_date = post_time.strftime("%d.%m.%Y %H:%M")
                if settings.post_text_format == "md":
                    if post_info.title:
                        text_content = f"# {post_info.title}\n"
                    else:
                        text_content = ""
                    text_content += parser.to_markdown() + "\n\n"
                    text_content += f"---\n\n*Published {fmt_date}*\n"
                else:
                    if post_info.title:
                        text_content = f"{post_info.title} \n\n"
                    else:
                        text_content = ""
                    text_content += parser.to_plain_text() + "\n\n"
                    text_content += f"[Published {fmt_date}]\n"
            except Exception as e:
                logger.error(
                    "Failed get post text content due unexpected error", exc_info=e
                )
                text_content = None

            if text_content:
                text_file_path = post_path / (
                    "content.txt"
                    if settings.post_text_format == "raw"
                    else "content.md"
                )
                if text_file_path.exists():
                    logger.info(f"Skip creating text file: {text_file_path} (already exists)")
                else:
                    logger.info(f"Creating text file: {text_file_path}")
                    async with aiofiles.open(text_file_path, "w", encoding="utf-8") as f:
                        await f.write(text_content)

            download_items = await self._prepare_download_tasks(
                post_path=post_path, post_info=post_info, settings=settings
            )

            self._count_files = len(download_items)
            with ProgressCounter(total=self._total_weight) as pbar:
                for media in download_items:
                    session = client.get_client_session()
                    try:
                        await self._download_file(
                            session=session,
                            file_url=media.final_url,
                            save_path=media.save_path,
                            pbar=pbar,
                            chunk_size=settings.chunk_size,
                        )
                    except Exception as e:
                        logger.error("Error downloading file", exc_info=e)
                        return self._fallback(TaskError.ERROR)
                    await asyncio.sleep(0.1)

            self._done = True
            self._percent = 100
            self._pending = False
            self._finished = True

        return None
