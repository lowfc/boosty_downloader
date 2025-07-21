import asyncio
from datetime import datetime
from datetime import UTC
from pathlib import Path
from typing import Optional

from boosty.api import get_all_media_by_type, get_all_posts, get_post_by_id
from boosty.wrappers.post_pool import PostPool
from core.config import conf
from boosty.wrappers.media_pool import MediaPool
from core.defs import ContentType
from core.downloader import Downloader
from core.logger import logger
from core.post_mapping.db import PostDBClient
from core.post_mapping.utils import ensure_post_database_exists, validate_windows_dir_name
from core.sync_data import SyncData
from core.utils import create_dir_if_not_exists, create_text_document, parse_offset_time


async def _fetch_media(
        media_type: ContentType,
        creator_name: str,
        use_cookie: bool,
        base_path: Path,
        sync_data: Optional[SyncData] = None,
        start_offset: Optional[str] = None,
):
    logger.debug(f"Start scanning media with start offset = {start_offset}")
    offset = start_offset
    eot = None
    fot = None
    is_last = False
    if sync_data:
        last_media_offset = await sync_data.get_last_media_offset(media_type)
        if last_media_offset:
            eot = int(last_media_offset)
    while not is_last:
        media_pool = MediaPool()
        is_last, got_offset = await get_all_media_by_type(
            content_type=media_type,
            creator_name=creator_name,
            media_pool=media_pool,
            use_cookie=use_cookie,
            offset=offset,
        )
        parsed_offset = parse_offset_time(got_offset)
        if fot is None and parsed_offset:
            fot = parsed_offset
        if eot and parsed_offset:
            if parsed_offset <= eot:
                logger.debug(f"Stop scanning media due to next api offset"
                             f" <= last saved offset: {parsed_offset} <= {eot}")
                is_last = True
        await asyncio.sleep(0.3)

        downloader = Downloader(
            media_pool=media_pool,
            base_path=base_path,
            max_parallel_downloads=conf.max_download_parallel,
            save_meta=conf.save_metadata
        )

        await downloader.download_by_content_type(media_type)

        if sync_data and offset:
            await sync_data.set_runtime_media_offset(media_type, offset)
            await sync_data.save()

        offset = got_offset

    if sync_data:
        await sync_data.set_runtime_media_offset(media_type, None)
        if await sync_data.get_last_media_offset(media_type) is None and fot:
            await sync_data.set_last_media_offset(media_type, str(fot))
        await sync_data.save()


async def fetch_and_save_media(
        creator_name: str,
        use_cookie: bool,
        base_path: Path,
        sync_data: Optional[SyncData] = None,
        image_start_offset: Optional[str] = None,
        audio_start_offset: Optional[str] = None,
        video_start_offset: Optional[str] = None,
):

    tasks_pull = []
    if conf.need_load_photo:
        tasks_pull.append(
            _fetch_media(
                media_type=ContentType.IMAGE,
                creator_name=creator_name,
                use_cookie=use_cookie,
                base_path=base_path,
                sync_data=sync_data,
                start_offset=image_start_offset,
            )
        )
    if conf.need_load_video:
        if not use_cookie:
            logger.warning("Some files may not be downloaded because authorization is missing.")
        tasks_pull.append(
            _fetch_media(
                media_type=ContentType.VIDEO,
                creator_name=creator_name,
                use_cookie=use_cookie,
                base_path=base_path,
                sync_data=sync_data,
                start_offset=video_start_offset,
            )
        )
    if conf.need_load_audio:
        tasks_pull.append(
            _fetch_media(
                media_type=ContentType.AUDIO,
                creator_name=creator_name,
                use_cookie=use_cookie,
                base_path=base_path,
                sync_data=sync_data,
                start_offset=audio_start_offset,
            )
        )
    if conf.need_load_files:
        logger.warning("ATTACHED FILES WILL NOT BE DOWNLOADED IN MEDIA STORAGE MODE")
        logger.warning("Use storage_type: post, for download attached files")
    await asyncio.gather(*tasks_pull)

    if sync_data:
        await sync_data.set_last_sync_utc(datetime.now(UTC))
        await sync_data.save()


async def fetch_and_save_posts(
        creator_name: str,
        use_cookie: bool,
        base_path: Path,
        cache_path: Path,
        start_offset: Optional[str] = None,
        sync_data: Optional[SyncData] = None,
):
    posts_path = base_path / "posts"
    create_dir_if_not_exists(posts_path)

    post_db_client = None
    if conf.enable_post_masquerade:
        post_db_path = cache_path / "post.db"
        if not ensure_post_database_exists(post_db_path):
            logger.critical("Can't create post db. "
                            "If this is not the first time you have encountered this problem, "
                            "disable this param in config: 'enable_post_masquerade'.")
            return
        post_db_client = PostDBClient(post_db_path)

    post_pool = PostPool()
    offset = start_offset
    eot = None
    fot = None
    if sync_data:
        last_posts_offset = await sync_data.get_last_posts_offset()
        if last_posts_offset:
            eot = int(last_posts_offset)
    while not post_pool.closed:
        await get_all_posts(creator_name=creator_name, post_pool=post_pool, use_cookie=use_cookie, offset=offset)
        parsed_offset = post_pool.parsed_offset
        if fot is None and parsed_offset:
            fot = parsed_offset
        if eot and parsed_offset:
            if parsed_offset <= eot:
                logger.debug(f"Stop scanning posts due to next api offset"
                             f" <= last saved offset: {parsed_offset} <= {eot}")
                post_pool.close()
        await asyncio.sleep(0.5)

        for post in post_pool.get_posts(offset):
            tasks = []
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
                if not use_cookie:
                    logger.warning("Some files may not be downloaded because authorization is missing.")
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

            await asyncio.gather(*tasks)
            if sync_data and offset:
                await sync_data.set_runtime_posts_offset(offset)
                await sync_data.save()

        offset = post_pool.offset

    if post_db_client:
        post_db_client.close()

    if sync_data:
        await sync_data.set_runtime_posts_offset(None)
        await sync_data.set_last_sync_utc(datetime.now(UTC))
        if await sync_data.get_last_posts_offset() is None and fot:
            await sync_data.set_last_posts_offset(str(fot))
        await sync_data.save()


async def fetch_and_save_lonely_post(
        creator_name: str,
        post_id: str,
        use_cookie: bool,
        base_path: Path,
        cache_path: Path,
        sync_data: Optional[SyncData] = None,
):
    posts_path = base_path / "posts"
    create_dir_if_not_exists(posts_path)

    post_db_client = None
    if conf.enable_post_masquerade:
        post_db_path = cache_path / "post.db"
        if not ensure_post_database_exists(post_db_path):
            logger.critical("Can't create post db. "
                            "If this is not the first time you have encountered this problem, "
                            "disable this param in config: 'enable_post_masquerade'.")
            return
        post_db_client = PostDBClient(post_db_path)

    post_pool = PostPool()
    await get_post_by_id(creator_name=creator_name, post_id=post_id, post_pool=post_pool, use_cookie=use_cookie)

    for post in post_pool.get_posts():
        tasks = []
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
            if not use_cookie:
                logger.warning("Some files may not be downloaded because authorization is missing.")
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

        await asyncio.gather(*tasks)

    if post_db_client:
        post_db_client.close()

    if sync_data:
        await sync_data.set_last_sync_utc(datetime.now(UTC))
        await sync_data.save()
