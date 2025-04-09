import asyncio
from datetime import datetime
from datetime import UTC
from pathlib import Path

from boosty.api import get_all_image_media, get_all_video_media, get_all_posts, get_all_audio_media
from boosty.wrappers.post_pool import PostPool
from core.config import conf
from boosty.wrappers.media_pool import MediaPool
from core.downloader import Downloader
from core.logger import logger
from core.post_mapping.db import PostDBClient
from core.post_mapping.utils import ensure_post_database_exists, validate_windows_dir_name
from core.sync_data import SyncData
from core.utils import create_dir_if_not_exists, create_text_document


async def fetch_and_save_media(creator_name: str, use_cookie: bool):
    base_path: Path = conf.sync_dir / creator_name
    create_dir_if_not_exists(base_path)
    cache_path = base_path / "__cache__"
    create_dir_if_not_exists(cache_path)
    sync_data = None
    if conf.sync_offset_save:
        sync_data_file_path = cache_path / conf.default_sd_file_name
        sync_data = SyncData.get_or_create_sync_data(sync_data_file_path, creator_name)
    media_pool = MediaPool()
    tasks_pull = []
    if conf.need_load_photo:
        tasks_pull.append(
            get_all_image_media(
                creator_name=creator_name,
                media_pool=media_pool,
                use_cookie=use_cookie,
                sync_data=sync_data
            )
        )
    if conf.need_load_video:
        tasks_pull.append(
            get_all_video_media(
                creator_name=creator_name,
                media_pool=media_pool,
                use_cookie=use_cookie,
                sync_data=sync_data
            )
        )
    if conf.need_load_audio:
        tasks_pull.append(
            get_all_audio_media(
                creator_name=creator_name,
                media_pool=media_pool,
                use_cookie=use_cookie,
                sync_data=sync_data
            )
        )
    if conf.need_load_files:
        logger.warning("ATTACHED FILES WILL NOT BE DOWNLOADED IN MEDIA STORAGE MODE")
        logger.warning("Use storage_type: post, for download attached files")
    await asyncio.gather(*tasks_pull)

    downloader = Downloader(
        media_pool=media_pool,
        base_path=base_path,
        max_parallel_downloads=conf.max_download_parallel,
        save_meta=conf.save_metadata
    )

    tasks = []
    if conf.need_load_photo:
        tasks.append(downloader.download_photos())

    if conf.need_load_video:
        tasks.append(downloader.download_videos())

    if conf.need_load_audio:
        if use_cookie:
            tasks.append(downloader.download_audios())
        else:
            logger.warning("Can't download audio without authorization. "
                           "Fill authorization fields in config to store audio files.")

    await asyncio.gather(*tasks)

    if sync_data:
        sync_data.last_sync_utc = datetime.now(UTC)
        sync_data.save()


async def fetch_and_save_posts(creator_name: str, use_cookie: bool):
    base_path: Path = conf.sync_dir / creator_name
    create_dir_if_not_exists(base_path)
    posts_path = base_path / "posts"
    cache_path = base_path / "__cache__"
    create_dir_if_not_exists(posts_path)
    create_dir_if_not_exists(cache_path)
    sync_data = None
    post_db_client = None
    if conf.sync_offset_save:
        sync_data_file_path = cache_path / conf.default_sd_file_name
        sync_data = SyncData.get_or_create_sync_data(sync_data_file_path, creator_name)
    if conf.enable_post_masquerade:
        post_db_path = cache_path / "post.db"
        if not ensure_post_database_exists(post_db_path):
            logger.critical("Can't create post db. "
                            "If this is not the first time you have encountered this problem, "
                            "disable this param in config: 'enable_post_masquerade'.")
            return
        post_db_client = PostDBClient(post_db_path)
    post_pool = PostPool()
    await get_all_posts(creator_name=creator_name, post_pool=post_pool, use_cookie=use_cookie, sync_data=sync_data)
    desired_post_id = conf.desired_post_id
    if desired_post_id:
        logger.info(f"SYNC ONLY ONE POST WITH ID = '{desired_post_id}'")
    tasks = []
    for post in post_pool.posts:
        if desired_post_id and post.id != desired_post_id:
            continue

        post_path = posts_path / post.id
        if conf.enable_post_masquerade:
            existing_post_data = post_db_client.get_post(post.id)
            if existing_post_data:
                post_path = Path(existing_post_data["post_path"])
            else:
                if len(post.title):
                    human_filename = validate_windows_dir_name(post.title)
                else:
                    human_filename = post.id
                post_path = posts_path / human_filename
                if len(post_db_client.get_posts_by_path(str(post_path))):
                    post_path = posts_path / (human_filename + "_" + post.id)
                post_db_client.create_post(creator_name, str(post_path), post.id)

        create_dir_if_not_exists(post_path)

        await create_text_document(
            path=post_path,
            content=post.get_contents_text(),
            ext="md" if conf.post_text_in_markdown else "txt"
        )

        downloader = Downloader(
            media_pool=post.media_pool,
            base_path=post_path,
            max_parallel_downloads=conf.max_download_parallel,
            save_meta=conf.save_metadata
        )

        if conf.need_load_photo:
            tasks.append(downloader.download_photos())

        if conf.need_load_video:
            tasks.append(downloader.download_videos())

        if conf.need_load_audio:
            if use_cookie:
                tasks.append(downloader.download_audios())
            else:
                logger.warning("Can't download audio without authorization. "
                               "Fill authorization fields in config to store audio files.")

        if conf.need_load_files:
            if use_cookie:
                tasks.append(downloader.download_files())
            else:
                logger.warning("Can't download attached files without authorization. "
                               "Fill authorization fields in config to store attached files.")

    if post_db_client:
        post_db_client.close()

    await asyncio.gather(*tasks)

    if sync_data:
        sync_data.last_sync_utc = datetime.now(UTC)
        sync_data.save()
