import asyncio
from msilib.schema import PublishComponent
import time
from pathlib import Path
from typing import Literal

import aiofiles
from aiohttp import ClientSession
from copy import copy

from boosty.enums import MediaType
from boosty.wrappers.post import Post
from boosty.wrappers.post_pool import PostPool
from core.config import conf
from boosty.wrappers.media_pool import MediaPool
from boosty.defs import DEFAULT_LIMIT, DEFAULT_LIMIT_BY, BOOSTY_API_BASE_URL, DEFAULT_HEADERS, DOWNLOAD_HEADERS
from core.defs import VIDEO_QUALITY
from core.logger import logger
from core.stat_tracker import stat_tracker


async def get_media_list(
    session: ClientSession,
    media_type: Literal["image", "video", "audio"],
    creator_name: str,
    use_cookie: bool,
    limit: int = DEFAULT_LIMIT,
    limit_by: str = DEFAULT_LIMIT_BY,
    offset: str = None
):
    params = {
        "type": media_type,
        "limit": limit,
        "limit_by": limit_by
    }
    if offset:
        params["offset"] = offset
    try:
        send_headers = copy(DEFAULT_HEADERS)
        if use_cookie and conf.ready_to_auth():
            send_headers["Cookie"] = conf.cookie
            send_headers["Authorization"] = conf.authorization
        url = BOOSTY_API_BASE_URL + f"/v1/blog/{creator_name}/media_album/"
        logger.info("GET " + url)
        resp = await session.get(
            url,
            params=params,
            headers=send_headers
        )
        result = await resp.json()
    except Exception as e:
        logger.error("Failed get media album", exc_info=e)
        result = None
    return result


async def get_all_image_media(creator_name: str, media_pool: MediaPool, use_cookie: bool):
    is_end = False
    offset = None
    errors = 0
    logger.info(f"get all photos for {creator_name}")
    async with ClientSession() as session:
        while not is_end:
            if errors > 10:
                logger.error("Break get media get due to errors")
                is_end = True
            resp = await get_media_list(
                session=session,
                creator_name=creator_name,
                media_type="image",
                use_cookie=use_cookie,
                offset=offset
            )
            if not resp:
                errors += 1
                continue
            extra = resp["extra"]
            media_posts = resp["data"]["mediaPosts"]
            for post in media_posts:
                if post["post"]["hasAccess"]:
                    for media in post["media"]:
                        media_pool.add_image(
                            _id=media["id"],
                            url=media["url"],
                            width=media["width"],
                            height=media["height"],
                        )
            if extra["isLast"]:
                is_end = True
            offset = extra["offset"]
            await asyncio.sleep(0.6)


async def get_all_audio_media(creator_name: str, media_pool: MediaPool, use_cookie: bool):
    is_end = False
    offset = None
    errors = 0
    logger.info(f"get all audios for {creator_name}")
    async with ClientSession() as session:
        while not is_end:
            if errors > 10:
                logger.error("Break get media get due to errors")
                is_end = True
            resp = await get_media_list(
                session=session,
                creator_name=creator_name,
                media_type="audio",
                use_cookie=use_cookie,
                offset=offset,
                limit_by="post"
            )
            if not resp:
                errors += 1
                continue
            extra = resp["extra"]
            media_posts = resp["data"]["mediaPosts"]
            for post in media_posts:
                if post["post"]["hasAccess"]:
                    for media in post["media"]:
                        media_pool.add_audio(
                            _id=media["id"],
                            url=media["url"] + post["post"].get("signedQuery", ""),
                            size_amount=media["size"]
                        )
            if extra["isLast"]:
                is_end = True
            offset = extra["offset"]
            await asyncio.sleep(0.6)


async def get_all_video_media(creator_name: str, media_pool: MediaPool, use_cookie: bool):
    is_end = False
    offset = None
    errors = 0
    logger.info(f"get all videos for {creator_name}")
    async with ClientSession() as session:
        while not is_end:
            if errors > 10:
                logger.error("Break media get due errors")
                is_end = True
            resp = await get_media_list(
                session=session,
                creator_name=creator_name,
                media_type="video",
                use_cookie=use_cookie,
                offset=offset
            )
            if not resp:
                errors += 1
                continue
            extra = resp["extra"]
            media_posts = resp["data"]["mediaPosts"]
            for post in media_posts:
                if post["post"]["hasAccess"]:
                    for media in post["media"]:
                        for url in media["playerUrls"]:
                            if url["type"] in VIDEO_QUALITY.keys() and url["url"] != "":
                                media_pool.add_video(
                                    _id=media["id"],
                                    url=url["url"],
                                    size_amount=VIDEO_QUALITY[url["type"]],
                                )
            if extra["isLast"]:
                is_end = True
            offset = extra["offset"]
            await asyncio.sleep(0.6)


async def download_file(url: str, path: Path) -> bool:
    if url == "":
        logger.warning(f"Empty URL for {path} file, skip")
        raise Exception("Empty url")
    try:
        async with ClientSession() as session:
            logger.info(f"preparing download {url}")
            headers = copy(DEFAULT_HEADERS)
            headers.update(DOWNLOAD_HEADERS)
            response = await session.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=conf.download_timeout
            )
            if response.status == 200:
                async with aiofiles.open(path, "wb") as file:
                    logger.info(f"saving file {path}")
                    length = response.content_length
                    logger.info(f"file size: {round(length / 1024 / 1024, 2)} (Mb)")
                    chunk_size = conf.download_chunk_size
                    downloaded_bytes = 0
                    last_log = time.monotonic()
                    start_time = last_log
                    logger.info(f"downloading file... chunk size={chunk_size}")
                    async for content in response.content.iter_chunked(chunk_size):
                        if time.monotonic() - last_log > 30:
                            downloaded = downloaded_bytes if downloaded_bytes > 0 else 1
                            download_percent = int(downloaded / length * 100)
                            last_log = time.monotonic()
                            elapsed = last_log - start_time
                            total_time = round(elapsed * (length / downloaded), 2)
                            estimated = total_time - elapsed
                            logger.info(f"still downloading file... {download_percent}% "
                                        f"(ela: {int(elapsed) // 60} min; eta: {int(estimated) // 60} min.)")
                        await file.write(content)  # noqa
                        downloaded_bytes += len(content)  # noqa
                        await asyncio.sleep(0)
                return True
            else:
                lg = f"non-200 status code ({response.status} for file {url}"
                logger.warning(lg)
                raise Exception(lg)
    except TimeoutError:
        lg = "[TimedOut] Failed download media due to timeout. " \
             "If file is large, try to set a higher value for the download_timeout parameter in config"
        logger.error(lg)
        raise Exception(lg)
    except Exception as e:
        logger.error(f"[{e.__class__.__name__}] Failed download media: {e}")
        stat_tracker.add_download_error(url)
        raise e


async def get_profile_stat(creator_name: str):
    url = BOOSTY_API_BASE_URL + f"/v1/blog/{creator_name}/media_album/counters/"
    async with ClientSession() as session:
        headers = copy(DEFAULT_HEADERS)
        response = await session.get(
            url,
            headers=headers
        )
        if response.status == 200:
            data = await response.json()
            stat_tracker.total_photos = data["data"]["mediaCounters"]["image"]
            stat_tracker.total_videos = data["data"]["mediaCounters"]["okVideo"]
            stat_tracker.total_audios = data["data"]["mediaCounters"]["audioFile"]
        else:
            logger.warning("FAILED GET PROFILE STAT")


async def get_post_list(
    session: ClientSession,
    creator_name: str,
    use_cookie: bool,
    limit: int = DEFAULT_LIMIT,
    limit_by: str = DEFAULT_LIMIT_BY,
    offset: str = None
):
    params = {
        "limit": limit,
        "limit_by": limit_by,
        "reply_limit": 1,
        "comments_limit": 0,
    }
    if offset:
        params["offset"] = offset
    try:
        send_headers = copy(DEFAULT_HEADERS)
        if use_cookie and conf.ready_to_auth():
            send_headers["Cookie"] = conf.cookie
            send_headers["Authorization"] = conf.authorization
        url = BOOSTY_API_BASE_URL + f"/v1/blog/{creator_name}/post/"
        logger.info("GET " + url)
        resp = await session.get(
            url,
            params=params,
            headers=send_headers
        )
        if resp.status != 200:
            raise Exception(f"{resp.status} on get posts")
        result = await resp.json()
    except Exception as e:
        logger.error("Failed get posts", exc_info=e)
        result = None
    return result


async def get_all_posts(creator_name: str, post_pool: PostPool, use_cookie: bool):
    is_end = False
    offset = None
    errors = 0
    logger.info(f"get all posts for {creator_name}")
    async with ClientSession() as session:
        while not is_end:
            if errors > 10:
                logger.error("Break posts get due errors")
                is_end = True
            resp = await get_post_list(
                session=session,
                creator_name=creator_name,
                use_cookie=use_cookie,
                offset=offset
            )
            if not resp:
                errors += 1
                continue
            extra = resp["extra"]
            posts = resp["data"]
            for post in posts:
                if post["hasAccess"]:
                    new_post = Post(
                        _id=post["id"],
                        title=post["title"],
                        created_at=post['createdAt'],
                        updated_at=post['updatedAt'],
                        publish_time=post['publishTime'])
                    for media in post["data"]:
                        if media["type"] == MediaType.VIDEO.value:
                            for url in media["playerUrls"]:
                                if url["type"] in VIDEO_QUALITY.keys() and url["url"] != "":
                                    new_post.media_pool.add_video(
                                        _id=media["id"],
                                        url=url["url"],
                                        size_amount=VIDEO_QUALITY[url["type"]],
                                    )
                        elif media["type"] == MediaType.IMAGE.value:
                            new_post.media_pool.add_image(
                                _id=media["id"],
                                url=media["url"],
                                width=media["width"],
                                height=media["height"]
                            )
                        elif media["type"] == MediaType.AUDIO.value:
                            new_post.media_pool.add_audio(
                                _id=media["id"],
                                url=media["url"] + post.get("signedQuery", ""),
                                size_amount=media["size"],
                            )
                        elif media["type"] == MediaType.TEXT:
                            if media["modificator"] == "":
                                new_post.add_marshaled_paragraph(media["content"])
                    for tag in post["tags"]:
                        new_post.add_tag(tag["id"], tag["title"])
                        post_pool.add_tag(tag["id"], tag["title"])
                    post_pool.add_post(new_post)
            if extra["isLast"]:
                is_end = True
            offset = extra["offset"]
            await asyncio.sleep(0.6)
