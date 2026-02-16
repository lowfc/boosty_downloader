import asyncio
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import aiofiles
from aiohttp import ClientSession
from tqdm.asyncio import tqdm_asyncio

from core.authorization_provider import AuthorizationProvider
from core.boosty.client import BoostyClient
from core.boosty.defs import BoostyImageDto, BoostyAudioDto, BoostyFileDto, BoostyVideoDto, VIDEO_QUALITY_GRADE, BoostyPostDto
from core.defs.common import DownloadingSettingsDto
from core.defs.tasks import TaskError
from core.draftjs_converter import DraftJsConverter
from core.logger import setup_logger
from core.utils import validate_windows_dir_name, sign_url, get_download_settings

logger = setup_logger()


@dataclass
class FinalDownloadTaskDto:
    final_url: str
    save_path: Path
    fetch_file_size: bool = False



class Task:
    """ Репрезентация таска фоновой загрузки файлов """

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

    def ready(self) -> bool:
        return not self._done and not self._pending and not self._error

    @property
    def percent(self) -> float:
        return self._percent / 100

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def fallen(self) -> bool:
        return self._finished and self._error

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
        pbar: tqdm_asyncio,
        fetch_file_size: bool = False,
        chunk_size: int = 153600,
    ):
        async with session:
            logger.info(f"Downloading file {file_url}")
            async with session.get(file_url) as response:
                logger.debug(f"Got response {response.status}")
                response.raise_for_status()
                if fetch_file_size:
                    """ Так как не для всех файлов заранее известен размер, фетчим его в рантайме """
                    self._total_weight += response.content_length
                    pbar.total = self._total_weight
                async with aiofiles.open(save_path, 'wb') as f:
                    logger.debug(f"Writing file {save_path}")
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            await f.write(chunk)
                            chunk_size = len(chunk)
                            self._downloaded_bytes += chunk_size
                            pbar.update(chunk_size)
                            total = pbar.total or chunk_size
                            self._percent = (pbar.n / total) * 100

    def _fallback(self, err: TaskError) -> None:
        self._error = True
        self.error_description = err
        self._finished = True
        self._pending = False

    def _prepare_download_tasks(
        self,
        post_path: Path,
        post_info: BoostyPostDto,
        settings: DownloadingSettingsDto,
    ) -> List[FinalDownloadTaskDto]:
        download_items = []
        for media in post_info.media:
            if isinstance(media, BoostyImageDto) and settings.need_download_photos:  # photo
                self._total_weight += media.size
                download_items.append(
                    FinalDownloadTaskDto(
                        final_url=media.url,
                        save_path=post_path / (media.id + ".jpg"),
                    )
                )

            elif isinstance(media, BoostyVideoDto) and settings.need_download_videos:  # video
                lborder_quality = VIDEO_QUALITY_GRADE.index(settings.preferred_video_size)
                for i in range(lborder_quality, len(VIDEO_QUALITY_GRADE)):
                    url_info = media.player_urls.get(VIDEO_QUALITY_GRADE[i])
                    if url_info:
                        path = post_path / validate_windows_dir_name(media.get_title())
                        download_items.append(
                            FinalDownloadTaskDto(
                                final_url=url_info.url,
                                save_path=path,
                                fetch_file_size=True
                            )
                        )
                        break

            elif isinstance(media, BoostyAudioDto) and settings.need_download_audios:  # audio
                if post_info.signed_query:
                    self._total_weight += media.size
                    path = post_path / validate_windows_dir_name(media.get_title())
                    download_items.append(
                        FinalDownloadTaskDto(
                            final_url=sign_url(media.url, post_info.signed_query),
                            save_path=path
                        )
                    )

            elif isinstance(media, BoostyFileDto) and settings.need_download_files:  # file
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
            auth_token = await AuthorizationProvider.get_authorization_if_valid()
            client = BoostyClient(
                chunk_size=settings.chunk_size,
                download_timeout=settings.download_timeout,
                auth_token=auth_token,
            )

            if self._post_info:
                post_info = self._post_info
            else:
                try:
                    post_info = await client.get_post_info(self.author, self.post_id)
                except Exception as e:
                    logger.error("Failed fetch post info due unexpected error", exc_info=e)
                    return self._fallback(TaskError.ERROR)


            if post_info.title:
                self.title = post_info.title

            self._percent = 2

            if not post_info.has_access:
                logger.error(f"User have no access to the post {self.post_id}, cancelled")
                return self._fallback(TaskError.ACCESS_DENIED)

            downloads_folder = Path(settings.downloads_folder)
            logger.info(f"Home dir: {downloads_folder}")

            try:
                if not os.path.isdir(settings.downloads_folder):
                    logger.error(f"Home directory does not exist: {settings.downloads_folder}, creating")
                    downloads_folder.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error("Failed create or check home directory", exc_info=e)
                return self._fallback(TaskError.NO_HOME_FOLDER)

            post_path = Path(settings.downloads_folder) / self.author / self.post_id
            if post_info.title:
                if title := validate_windows_dir_name(post_info.title):
                    post_path = Path(settings.downloads_folder) / self.author / (title + "_" + self.post_id)

            self.path = post_path
            if os.path.isdir(post_path):
                if len(os.listdir(post_path)) > 0:
                    logger.error(f"Post directory already exists: {post_path}")
                    return self._fallback(TaskError.ALREADY_EXISTS)
            else:
                post_path.mkdir(parents=True)
                logger.info(f"Post directory created: {post_path}")

            try:
                parser = DraftJsConverter(post_info.text_content.content)
                post_time = datetime.fromtimestamp(post_info.publish_time)
                fmt_date = post_time.strftime('%d.%m.%Y %H:%M')
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
                logger.error("Failed get post text content due unexpected error", exc_info=e)
                text_content = None

            if text_content:
                text_file_path = post_path / ("content.txt" if settings.post_text_format == "raw" else "content.md")
                logger.info(f"Creating text file: {text_file_path}")
                async with aiofiles.open(text_file_path, 'w', encoding="utf-8") as f:
                    await f.write(text_content)

            download_items = self._prepare_download_tasks(
                post_path=post_path,
                post_info=post_info,
                settings=settings
            )
            self._percent = 5

            self._count_files = len(download_items)
            with tqdm_asyncio(total=self._total_weight, unit='B', unit_scale=True) as pbar:
                for media in download_items:
                    session = client.get_client_session()
                    try:
                        await self._download_file(
                            session=session,
                            file_url=media.final_url,
                            save_path=media.save_path,
                            pbar=pbar,
                            fetch_file_size=media.fetch_file_size,
                            chunk_size=settings.chunk_size,
                        )
                    except Exception as e:
                        logger.error("Error downloading file", exc_info=e)
                        return self._fallback(TaskError.ERROR)
                    await asyncio.sleep(.1)

            self._done = True
            self._percent = 100
            self._pending = False
            self._finished = True

        return None
