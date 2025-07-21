import asyncio
import os
from pathlib import Path
from typing import Literal, Any, Optional, Awaitable

from boosty.api import download_file
from boosty.wrappers.media_pool import MediaPool
from core.defs import ContentType
from core.logger import logger
from core.meta import write_video_metadata
from core.utils import create_dir_if_not_exists
from core.stat_tracker import stat_tracker


class Downloader:
    def __init__(
            self,
            media_pool: MediaPool,
            base_path: Path,
            max_parallel_downloads: int = 10,
            save_meta: bool = False,
    ):
        self.media_pool = media_pool
        self.base_path = base_path
        self._max_parallel_downloads = max_parallel_downloads
        self._save_meta = save_meta
        self._semaphore = asyncio.Semaphore(max_parallel_downloads)

    async def _download_file_if_not_exists(
            self,
            file_url: str,
            path: Path,
            meta_writer: Optional[Awaitable] = None
    ) -> bool:
        if os.path.isfile(path):
            logger.debug(f"pass saving file {path}: already exists")
            return False
        logger.info(f"will save file: {path}")
        result = await download_file(file_url, path)
        if self._save_meta and result and meta_writer:
            logger.info(f"writing metadata to file {path}")
            await meta_writer
        return result

    async def _get_file_and_raise_stat(
            self,
            url: str,
            path_file: Path,
            _t: Literal["p", "v", "a", "f"],
            metadata: dict[str, Any] | None = None
    ):
        match _t:
            case "p":
                passed = stat_tracker.add_passed_photo
                downloaded = stat_tracker.add_downloaded_photo
                error = stat_tracker.add_error_photo
                meta_writer = None
            case "v":
                passed = stat_tracker.add_passed_video
                downloaded = stat_tracker.add_downloaded_video
                error = stat_tracker.add_error_video
                meta_writer = write_video_metadata(path_file, metadata)
            case "a":
                passed = stat_tracker.add_passed_audio
                downloaded = stat_tracker.add_downloaded_audio
                error = stat_tracker.add_error_audio
                meta_writer = None
            case "f":
                passed = stat_tracker.add_passed_file
                downloaded = stat_tracker.add_downloaded_file
                error = stat_tracker.add_error_file
                meta_writer = None
            case _:
                logger.warning(f"Unknown _t: {_t}")
                return

        async with self._semaphore:
            try:
                if await self._download_file_if_not_exists(url, path_file, meta_writer):
                    downloaded()
                else:
                    passed()
            except Exception as e:
                logger.warning(f"err download {url}", exc_info=e)
                error()

    async def download_by_content_type(self, content_type: ContentType):
        match content_type:
            case ContentType.IMAGE:
                await self.download_photos()
                return
            case ContentType.VIDEO:
                await self.download_videos()
                return
            case ContentType.AUDIO:
                await self.download_audios()
                return

    async def download_photos(self):
        tasks = []
        photo_path = self.base_path / "photos"
        create_dir_if_not_exists(photo_path)
        images = self.media_pool.get_images()
        for image in images:
            path = photo_path / (image["id"] + ".jpg")
            tasks.append(self._get_file_and_raise_stat(image["url"], path, "p"))
        await asyncio.gather(*tasks)

    async def download_videos(self):
        tasks = []
        video_path = self.base_path / "videos"
        create_dir_if_not_exists(video_path)
        videos = self.media_pool.get_videos()
        for video in videos:
            path = video_path / (video["id"] + ".mp4")
            tasks.append(self._get_file_and_raise_stat(video["url"], path, "v", video.get("meta")))
        await asyncio.gather(*tasks)

    async def download_audios(self):
        tasks = []
        audio_path = self.base_path / "audios"
        create_dir_if_not_exists(audio_path)
        audios = self.media_pool.get_audios()
        for audio in audios:
            path = audio_path / (audio["id"] + ".mp3")
            tasks.append(self._get_file_and_raise_stat(audio["url"], path, "a"))
        await asyncio.gather(*tasks)

    async def download_files(self):
        tasks = []
        files_path = self.base_path / "files"
        create_dir_if_not_exists(files_path)
        files = self.media_pool.get_files()
        for file in files:
            path = files_path / file["title"]
            tasks.append(self._get_file_and_raise_stat(file["url"], path, "f"))
        await asyncio.gather(*tasks)
