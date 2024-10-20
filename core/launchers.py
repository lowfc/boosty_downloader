import asyncio
from pathlib import Path
from typing import Literal

from boosty.api import get_all_image_media, get_all_video_media, get_all_posts, get_all_audio_media
from boosty.wrappers.post_pool import PostPool
from core.config import conf
from boosty.wrappers.media_pool import MediaPool
from core.logger import logger
from core.stat_tracker import stat_tracker, StatTracker
from core.utils import create_dir_if_not_exists, download_file_if_not_exists, create_text_document


async def get_file_and_raise_stat(url: str, path_file: Path, tracker: StatTracker, _t: Literal["p", "v", "a"]):
    match _t:
        case "p":
            passed = tracker.add_passed_photo
            downloaded = tracker.add_downloaded_photo
            error = tracker.add_error_photo
        case "v":
            passed = tracker.add_passed_video
            downloaded = tracker.add_downloaded_video
            error = tracker.add_error_video
        case "a":
            passed = tracker.add_passed_audio
            downloaded = tracker.add_downloaded_audio
            error = tracker.add_error_audio
        case _:
            logger.warning(f"Unknown _t: {_t}")
            return

    try:
        if await download_file_if_not_exists(url, path_file):
            downloaded()
        else:
            passed()
    except Exception as e:
        logger.warning(f"err download {url}", exc_info=e)
        error()


async def fetch_and_save_media(creator_name: str, use_cookie: bool):
    base_path: Path = conf.sync_dir / creator_name
    create_dir_if_not_exists(base_path)
    photo_path = base_path / "photos"
    video_path = base_path / "videos"
    audio_path = base_path / "audios"
    create_dir_if_not_exists(photo_path)
    create_dir_if_not_exists(video_path)
    create_dir_if_not_exists(audio_path)
    media_pool = MediaPool()
    tasks = []
    if conf.need_load_photo:
        tasks.append(
            get_all_image_media(creator_name=creator_name, media_pool=media_pool, use_cookie=use_cookie)
        )
    if conf.need_load_video:
        tasks.append(
            get_all_video_media(creator_name=creator_name, media_pool=media_pool, use_cookie=use_cookie)
        )
    if conf.need_load_audio:
        tasks.append(
            get_all_audio_media(creator_name=creator_name, media_pool=media_pool, use_cookie=use_cookie)
        )
    await asyncio.gather(*tasks)
    images = media_pool.get_images()
    videos = media_pool.get_videos()
    audios = media_pool.get_audios()
    coros = []

    grp_photos = []
    i = 0
    for img in images:
        path = photo_path / (img["id"] + ".jpg")
        grp_photos.append(get_file_and_raise_stat(img["url"], path, stat_tracker, "p"))
        i += 1
        if i >= conf.max_download_parallel:
            coros.append(grp_photos)
            grp_photos = []
            i = 0
    if len(grp_photos):
        coros.append(grp_photos)

    grp_videos = []
    i = 0
    for video in videos:
        path = video_path / (video["id"] + ".mp4")
        grp_videos.append(get_file_and_raise_stat(video["url"], path, stat_tracker, "v"))
        i += 1
        if i == conf.max_download_parallel:
            coros.append(grp_videos)
            grp_videos = []
            i = 0
    if len(grp_videos):
        coros.append(grp_videos)

    grp_audios = []
    i = 0
    for audio in audios:
        path = audio_path / (audio["id"] + ".mp3")
        grp_audios.append(get_file_and_raise_stat(audio["url"], path, stat_tracker, "a"))
        i += 1
        if i == conf.max_download_parallel:
            coros.append(grp_audios)
            grp_audios = []
            i = 0
    if len(grp_audios):
        coros.append(grp_audios)

    for grp in coros:
        await asyncio.gather(*grp)
        await asyncio.sleep(0)


async def fetch_and_save_posts(creator_name: str, use_cookie: bool):
    base_path: Path = conf.sync_dir / creator_name
    create_dir_if_not_exists(base_path)
    posts_path = base_path / "posts"
    create_dir_if_not_exists(posts_path)
    post_pool = PostPool()
    await get_all_posts(creator_name=creator_name, post_pool=post_pool, use_cookie=use_cookie)
    await create_text_document(path=base_path, content=post_pool.get_tags_text(), name="tags")
    coros = []
    desired_post_id = conf.desired_post_id
    if desired_post_id:
        logger.info(f"SYNC ONLY ONE POST WITH ID = '{desired_post_id}'")
    for post in post_pool.posts:
        if desired_post_id and post.id != desired_post_id:
            continue
        post_path = posts_path / post.id
        create_dir_if_not_exists(post_path)
        photo_path = post_path / "photos"
        video_path = post_path / "videos"
        audio_path = post_path / "audios"
        create_dir_if_not_exists(photo_path)
        create_dir_if_not_exists(video_path)
        create_dir_if_not_exists(audio_path)
        await create_text_document(path=post_path, content=post.get_contents_text(), name="contents")
        await create_text_document(path=post_path, content=post.get_tags_text(), name="tags")
        await create_text_document(path=post_path, content=post.get_attributes_text(), name="attributes")

        images = post.media_pool.get_images()
        grp_photos = []
        i = 0
        for img in images:
            path = photo_path / (img["id"] + ".jpg")
            grp_photos.append(get_file_and_raise_stat(img["url"], path, stat_tracker, "p"))
            i += 1
            if i >= conf.max_download_parallel:
                coros.append(grp_photos)
                grp_photos = []
                i = 0
        if len(grp_photos):
            coros.append(grp_photos)

        videos = post.media_pool.get_videos()
        grp_videos = []
        i = 0
        for video in videos:
            path = video_path / (video["id"] + ".mp4")
            grp_videos.append(get_file_and_raise_stat(video["url"], path, stat_tracker, "v"))
            i += 1
            if i == conf.max_download_parallel:
                coros.append(grp_videos)
                grp_videos = []
                i = 0
        if len(grp_videos):
            coros.append(grp_videos)

        audios = post.media_pool.get_audios()
        grp_audios = []
        i = 0
        for audio in audios:
            path = audio_path / (audio["id"] + ".mp3")
            grp_audios.append(get_file_and_raise_stat(audio["url"], path, stat_tracker, "a"))
            i += 1
            if i == conf.max_download_parallel:
                coros.append(grp_audios)
                grp_audios = []
                i = 0
        if len(grp_audios):
            coros.append(grp_audios)

    for grp in coros:
        await asyncio.gather(*grp)
        await asyncio.sleep(0)

