import asyncio
from pathlib import Path
from typing import Literal

from aiohttp import ClientSession
from copy import copy

from core.config import conf
from boosty.base import MediaPool
from boosty.defs import DEFAULT_LIMIT, DEFAULT_LIMIT_BY, BOOSTY_API_BASE_URL, DEFAULT_HEADERS
from core.defs import VIDEO_QUALITY, DOWNLOAD_HEADERS
from core.logger import logger
from core.stat import Stat, stat_tracker


async def get_media_list(
    session: ClientSession,
    media_type: Literal["image", "video"],
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
                logger.error("Break media get due errors")
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


async def download_file(url: str, path: Path):
    if url == "":
        logger.warning(f"Empty URL for {path} file, skip")
        return
    async with ClientSession() as session:
        logger.info(f"downloading file {url}")
        headers = copy(DEFAULT_HEADERS)
        headers.update(DOWNLOAD_HEADERS)
        response = await session.get(
            url,
            headers=headers
        )
        if response.status == 200:
            logger.info(f"saving file {path}")
            cont = await response.read()
            with open(path, "wb") as file:
                file.write(cont)
        else:
            logger.warning(f"non-200 status code ({response.status} for file {url}")


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
        else:
            logger.warning("FAILED GET PROFILE STAT")
