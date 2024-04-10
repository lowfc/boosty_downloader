import asyncio
import os.path
import sys
from pathlib import Path

from boosty.api import get_all_video_media, get_all_image_media
from boosty.base import MediaPool
from core.config import conf
from core.logger import logger
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
    for img in images:
        path = photo_path / (img["id"] + ".jpg")
        coros.append(download_file_if_not_exists(img["url"], path))
    for video in videos:
        path = video_path / (video["id"] + ".mp4")
        coros.append(download_file_if_not_exists(video["url"], path))
    await asyncio.gather(*coros)

if __name__ == "__main__":
    logger.info(f"starting sync media...")
    logger.info(f"creator: {conf.creator_name}")
    logger.info(f"check path: {conf.sync_dir}")
    uah = conf.authorization != "" and conf.cookie != ""
    logger.info(f"use authorization headers: {uah}")
    if not os.path.isdir(conf.sync_dir):
        logger.critical(f"path {conf.sync_dir} is not exists. Create it and try again.")
        sys.exit(1)
    asyncio.run(fetch_and_save(conf.sync_dir / conf.creator_name))
