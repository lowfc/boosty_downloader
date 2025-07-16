import asyncio
import time
from pathlib import Path
from typing import Optional, Any

import aiofiles
from aiohttp import ClientSession
from copy import copy

from boosty.defs import MediaType
from boosty.wrappers.post import Post
from boosty.wrappers.post_pool import PostPool
from core.config import conf
from boosty.wrappers.media_pool import MediaPool
from boosty.defs import DEFAULT_LIMIT, DEFAULT_LIMIT_BY, BOOSTY_API_BASE_URL, DEFAULT_HEADERS, DOWNLOAD_HEADERS
from core.defs import VIDEO_QUALITY, ContentType
from core.logger import logger
from core.meta import parse_metadata
from core.stat_tracker import stat_tracker


async def get_media_list(
    session: ClientSession,
    content_type: ContentType,
    creator_name: str,
    use_cookie: bool,
    limit: int = DEFAULT_LIMIT,
    limit_by: str = DEFAULT_LIMIT_BY,
    offset: str = None
):
    if isinstance(content_type, ContentType):
        media_type = content_type.value
    else:
        media_type = content_type
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
        logger.info("GET " + url + f" offset={offset}")
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


async def get_all_media_by_type(
    content_type: ContentType,
    creator_name: str,
    media_pool: MediaPool,
    use_cookie: bool,
    offset: Optional[str] = None
) -> tuple[Any, Any]:
    logger.info(f"get all {content_type.value} for {creator_name}")
    async with ClientSession() as session:
        for i in range(10):
            resp = await get_media_list(
                session=session,
                creator_name=creator_name,
                content_type=content_type,
                use_cookie=use_cookie,
                offset=offset
            )
            if not resp:
                logger.warning(f"get all {content_type.value} for {creator_name} failed due unknown reason, rerun...")
                await asyncio.sleep(0.3)
                continue
            extra = resp["extra"]
            media_posts = resp["data"]["mediaPosts"]
            for post in media_posts:
                if post["post"]["hasAccess"]:
                    for media in post["media"]:
                        if content_type == ContentType.IMAGE:
                            media_pool.add_image(
                                _id=media["id"],
                                url=media["url"],
                                width=media["width"],
                                height=media["height"],
                            )
                        elif content_type == ContentType.AUDIO:
                            media_pool.add_audio(
                                _id=media["id"],
                                url=media["url"] + post["post"].get("signedQuery", ""),
                                size_amount=media["size"]
                            )
                        elif content_type == ContentType.VIDEO:
                            for url in media["playerUrls"]:
                                if url["type"] in VIDEO_QUALITY.keys() and url["url"] != "":
                                    media_pool.add_video(
                                        _id=media["id"],
                                        url=url["url"],
                                        size_amount=VIDEO_QUALITY[url["type"]],
                                        meta=parse_metadata(post["post"], media),
                                    )
            return extra["isLast"], extra["offset"]
    return True, None


async def download_file(url: str, path: Path) -> bool:
    if url == "":
        logger.warning(f"Empty URL for {path} file, skip")
        raise Exception("Empty url")
    try:
        async with ClientSession() as session:
            headers = copy(DEFAULT_HEADERS)
            headers.update(DOWNLOAD_HEADERS)
            length = 0
            for i in range(3):
                logger.info(f"preparing download {url}")
                response = await session.get(
                    url,
                    headers=headers,
                    allow_redirects=True,
                    timeout=conf.download_timeout
                )
                if response.status == 200:
                    length = response.content_length
                    if length < 10000:
                        logger.warning("Seems like here is bad download, lets try again")
                        await asyncio.sleep(0.5)
                        continue
                break

            if response.status == 200:
                async with aiofiles.open(path, "wb") as file:
                    logger.info(f"saving file {path}")
                    logger.info(f"file size: {round(length / 1024 / 1024, 2)} (Mb)")
                    chunk_size = conf.download_chunk_size
                    downloaded_bytes = 0
                    last_log = time.monotonic()
                    start_time = last_log
                    logger.info(f"downloading file... chunk size={chunk_size}")
                    async for content in response.content.iter_chunked(chunk_size):
                        if time.monotonic() - last_log > 30.0:
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
    offset: str = None,
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


async def get_all_posts(
    creator_name: str,
    post_pool: PostPool,
    use_cookie: bool,
    offset: Optional[str] = None,
):
    logger.info(f"get posts for {creator_name}")
    async with ClientSession() as session:
        for i in range(10):
            resp = await get_post_list(
                session=session,
                creator_name=creator_name,
                use_cookie=use_cookie,
                offset=offset
            )
            if not resp:
                continue
            extra = resp["extra"]
            posts = resp["data"]
            for post in posts:
                if post["hasAccess"]:
                    new_post = Post(
                        _id=post["id"],
                        title=post["title"],
                        markdown_text=conf.post_text_in_markdown,
                        publish_time=post["publishTime"]
                    )
                    signed_query = post.get("signedQuery", "")
                    for media in post["data"]:
                        if media["type"] == MediaType.VIDEO.value:
                            for url in media["playerUrls"]:
                                if url["type"] in VIDEO_QUALITY.keys() and url["url"] != "":
                                    new_post.media_pool.add_video(
                                        _id=media["id"],
                                        url=url["url"],
                                        size_amount=VIDEO_QUALITY[url["type"]],
                                        meta=parse_metadata(post, media),
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
                                url=media["url"] + signed_query,
                                size_amount=media["size"],
                            )
                        elif media["type"] == MediaType.FILE.value:
                            new_post.media_pool.add_file(
                                _id=media["id"],
                                url=media["url"] + signed_query,
                                size_amount=media["size"],
                                title=media["title"]
                            )
                        elif media["type"] == MediaType.TEXT.value:
                            if media["modificator"] == "":
                                new_post.add_marshaled_text(media["content"])
                            elif media["modificator"] == "BLOCK_END":
                                new_post.add_block_end()
                        elif media["type"] == MediaType.LINK.value:
                            new_post.add_link(media["content"], media["url"])
                    post_pool.add_post(new_post, offset)
            if extra["isLast"]:
                post_pool.close()
            post_pool.set_offset(extra["offset"])
            return
        logger.error("Break posts get due errors")


async def fetch_post_by_id(
    session: ClientSession,
    creator_name: str,
    post_id: str,
    use_cookie: bool,
):
    try:
        send_headers = copy(DEFAULT_HEADERS)
        if use_cookie and conf.ready_to_auth():
            send_headers["Cookie"] = conf.cookie
            send_headers["Authorization"] = conf.authorization
        url = BOOSTY_API_BASE_URL + f"/v1/blog/{creator_name}/post/{post_id}"
        logger.info("GET " + url)
        resp = await session.get(
            url,
            headers=send_headers
        )
        if resp.status != 200:
            raise Exception(f"{resp.status} on get post by id")
        result = await resp.json()
    except Exception as e:
        logger.error("Failed get posts", exc_info=e)
        result = None
    return result


async def get_post_by_id(
    creator_name: str,
    post_id: str,
    post_pool: PostPool,
    use_cookie: bool,
    offset: Optional[str] = None,
):
    logger.info(f"get posts for {creator_name}")
    async with ClientSession() as session:
        for i in range(10):
            resp = await fetch_post_by_id(
                session=session,
                creator_name=creator_name,
                post_id=post_id,
                use_cookie=use_cookie,
            )
            if not resp:
                continue

            if resp["hasAccess"]:
                new_post = Post(
                    _id=resp["id"],
                    title=resp["title"],
                    markdown_text=conf.post_text_in_markdown,
                    publish_time=resp["publishTime"]
                )
                signed_query = resp.get("signedQuery", "")
                for media in resp["data"]:
                    if media["type"] == MediaType.VIDEO.value:
                        for url in media["playerUrls"]:
                            if url["type"] in VIDEO_QUALITY.keys() and url["url"] != "":
                                new_post.media_pool.add_video(
                                    _id=media["id"],
                                    url=url["url"],
                                    size_amount=VIDEO_QUALITY[url["type"]],
                                    meta=parse_metadata(resp, media),
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
                            url=media["url"] + signed_query,
                            size_amount=media["size"],
                        )
                    elif media["type"] == MediaType.FILE.value:
                        new_post.media_pool.add_file(
                            _id=media["id"],
                            url=media["url"] + signed_query,
                            size_amount=media["size"],
                            title=media["title"]
                        )
                    elif media["type"] == MediaType.TEXT.value:
                        if media["modificator"] == "":
                            new_post.add_marshaled_text(media["content"])
                        elif media["modificator"] == "BLOCK_END":
                            new_post.add_block_end()
                    elif media["type"] == MediaType.LINK.value:
                        new_post.add_link(media["content"], media["url"])
                post_pool.add_post(new_post, offset)
            post_pool.close()
            return
