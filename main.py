import asyncio
import os.path
import sys
from pathlib import Path
from typing import Literal

from boosty.api import get_all_video_media, get_all_image_media, get_profile_stat
from boosty.base import MediaPool
from core.config import conf
from core.logger import logger
from core.stat import stat_tracker, Stat
from core.utils import create_dir_if_not_exists, download_file_if_not_exists


async def fetch_and_save(base_path: Path):
    create_dir_if_not_exists(base_path)
    photo_path = base_path / "photos"
    video_path = base_path / "videos"
    create_dir_if_not_exists(photo_path)
    create_dir_if_not_exists(video_path)
    media_pool = MediaPool()
    await asyncio.gather(
        get_all_image_media(creator_name=conf.creator_name, media_pool=media_pool),
        get_all_video_media(creator_name=conf.creator_name, media_pool=media_pool),
    )
    images = media_pool.get_images()
    videos = media_pool.get_videos()
    coros = []

    async def get_file_and_raise_stat(url: str, path_file: Path, tracker: Stat, _t: Literal["p", "v"]):
        passed = tracker.add_passed_photo if _t == "p" else tracker.add_passed_video
        downloaded = tracker.add_downloaded_photo if _t == "p" else tracker.add_downloaded_video

        if await download_file_if_not_exists(url, path_file):
            downloaded()
        else:
            passed()

    for img in images:
        path = photo_path / (img["id"] + ".jpg")
        coros.append(get_file_and_raise_stat(img["url"], path, stat_tracker, "p"))
    for video in videos:
        path = video_path / (video["id"] + ".mp4")
        coros.append(get_file_and_raise_stat(video["url"], path, stat_tracker, "v"))
    await asyncio.gather(*coros)


async def main():
    await fetch_and_save(conf.sync_dir / conf.creator_name)
    await get_profile_stat(conf.creator_name, stat_tracker)


if __name__ == "__main__":
    logger.info(f"starting sync media...")
    logger.info(f"creator: {conf.creator_name}")
    logger.info(f"check path: {conf.sync_dir}")
    uah = conf.authorization != "" and conf.cookie != ""
    logger.info(f"use authorization headers: {uah}")
    if not os.path.isdir(conf.sync_dir):
        logger.critical(f"path {conf.sync_dir} is not exists. Create it and try again.")
        sys.exit(1)

    loop = asyncio.get_event_loop()
    if loop.is_closed():
        asyncio.set_event_loop(asyncio.new_event_loop())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

    print(f"\n\n ====== SUMMARY ====== \n{stat_tracker}")
