import asyncio
import os
from pathlib import Path
from typing import Optional, Union

import aiofiles
import flet as ft
from aiohttp import ClientSession
from tqdm.asyncio import tqdm_asyncio

from core.boosty.client import BoostyClient
from core.boosty.defs import BoostyImageDto, BoostyPlayerUrlDto, BoostyAudioDto, BoostyFileDto, BoostyVideoDto, \
    BoostyTextDto, BoostyLinkDto
from core.defs.tasks import TaskError
from core.logger import setup_logger
from core.utils import get_destination_folder, validate_windows_dir_name

logger = setup_logger(__name__)


class Task:
    def __init__(self, semaphore: asyncio.Semaphore, author: str, post_id: str):
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
        """ Some preflight here """
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
        """ Some preflight here """
        self._percent = 0
        self._error = False
        self.error_description = None
        self._finished = False
        self._task = None
        self.launch()

    async def _download_file(
        self,
        session: ClientSession,
        file_url: str,
        save_path: str,
        pbar: tqdm_asyncio,
        chunk_size: int = 153600,
    ):
        async with session:
            logger.info(f"Downloading file {file_url}")
            async with session.get(file_url) as response:
                logger.debug(f"Got response {response.status}")
                async with aiofiles.open(save_path, 'wb') as f:
                    logger.debug(f"Writing file {save_path}")
                    async for chunk in response.content.iter_chunked(chunk_size):
                        if chunk:
                            await f.write(chunk)
                            self._downloaded_bytes += len(chunk)
                            pbar.update(len(chunk))
                            self._percent = (pbar.n / pbar.total) * 100

    async def _run(self):
        if self._done or self._pending:
            return
        self._pending = True
        async with self._semaphore:
            need_download_photos = await ft.SharedPreferences().get("need-download-photos") == "True"
            if need_download_photos is None:
                need_download_photos = True
            need_download_videos = await ft.SharedPreferences().get("need-download-videos") == "True"
            if need_download_videos is None:
                need_download_videos = True
            need_download_audios = await ft.SharedPreferences().get("need-download-audios") == "True"
            if need_download_audios is None:
                need_download_audios = True
            need_download_files = await ft.SharedPreferences().get("need-download-files") == "True"
            if need_download_files is None:
                need_download_files = True

            chunk_size = int(await ft.SharedPreferences().get("download-chunk-size") or 153600)
            download_timeout = int(await ft.SharedPreferences().get("download-timeout") or 3600)
            preferred_video_size = await ft.SharedPreferences().get("preferred-video-size") or "max"
            post_text_format = await ft.SharedPreferences().get("post-text-format") or "md"
            downloads_folder = await get_destination_folder()

            self._percent = 2

            client = BoostyClient(
                chunk_size=chunk_size,
                download_timeout=download_timeout,
                post_text_in_md=post_text_format == "md",
            )
            try:
                post_info = await client.get_post_info(self.author, self.post_id)
            except Exception as e:
                logger.error("Failed fetch post info due unexpected error", exc_info=e)
                self._error = True
                self._finished = True
                self._pending = False
                self.error_description = TaskError.ERROR
                return
            if post_info.title:
                self.title = post_info.title

            if not post_info.has_access:
                logger.error(f"User have no access to the post {self.post_id}, cancelled")
                self._error = True
                self._finished = True
                self._pending = False
                self.error_description = TaskError.ACCESS_DENIED
                return

            logger.info(f"Home dir: {downloads_folder}")
            if not os.path.isdir(downloads_folder):
                logger.error(f"Home directory does not exist: {downloads_folder}")
                self._error = True
                self._finished = True
                self._pending = False
                self.error_description = TaskError.NO_HOME_FOLDER
                return

            post_path = Path(downloads_folder) / self.author / self.post_id
            if post_info.title:
                title = validate_windows_dir_name(post_info.title)
                if title:
                    post_path = Path(downloads_folder) / self.author / (title + "_" + self.post_id)

            if os.path.isdir(post_path):
                if len(os.listdir(post_path)) > 0:
                    logger.error(f"Post directory already exists: {post_path}")
                    self._error = True
                    self._finished = True
                    self._pending = False
                    self.error_description = TaskError.ALREADY_EXISTS
                    return
            else:
                post_path.mkdir(parents=True)
                logger.info(f"Post directory created: {post_path}")

            self.path = post_path
            self._percent = 5
            download_items = []
            for media in post_info.media:
                if isinstance(media, BoostyImageDto) and need_download_photos:
                    self._total_weight += media.size
                    download_items.append((media.url, post_path / (media.id + ".jpg")))
                elif isinstance(media, BoostyVideoDto) and need_download_videos:
                    ...
                elif isinstance(media, BoostyAudioDto) and need_download_audios:
                    ...
                elif isinstance(media, BoostyFileDto) and need_download_files:
                    ...
                elif isinstance(media, BoostyLinkDto):
                    ...
                elif isinstance(media, BoostyTextDto):
                    ...

            self._count_files = len(download_items)
            with tqdm_asyncio(total=self._total_weight, unit='B', unit_scale=True) as pbar:
                for media in download_items:
                    session = client.get_client_session()
                    await self._download_file(
                        session=session,
                        file_url=media[0],
                        save_path=media[1],
                        pbar=pbar,
                        chunk_size=chunk_size,
                    )
                    await asyncio.sleep(.1)

            self._done = True
            self._percent = 100
            self._pending = False
            self._finished = True
