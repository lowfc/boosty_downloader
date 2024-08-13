import sys

try:
    import asyncio
    import os.path
    from pathlib import Path
    from typing import Literal

    from boosty.api import get_all_video_media, get_all_image_media, get_profile_stat
    from boosty.base import MediaPool
    from core.config import conf
    from core.exceptions import SyncCancelledExc, ConfigMalformedExc
    from core.logger import logger
    from core.stat import stat_tracker, Stat
    from core.utils import create_dir_if_not_exists, download_file_if_not_exists, parse_creator_name, parse_bool, \
        print_summary
except Exception as e:
    print(f"[{e.__class__.__name__}] App stopped ({e})")
    input("Press enter to exit...")
    sys.exit(1)


async def fetch_and_save(creator_name: str, use_cookie: bool):
    base_path: Path = conf.sync_dir / creator_name
    create_dir_if_not_exists(base_path)
    photo_path = base_path / "photos"
    video_path = base_path / "videos"
    create_dir_if_not_exists(photo_path)
    create_dir_if_not_exists(video_path)
    media_pool = MediaPool()
    await asyncio.gather(
        get_all_image_media(creator_name=creator_name, media_pool=media_pool, use_cookie=use_cookie),
        get_all_video_media(creator_name=creator_name, media_pool=media_pool, use_cookie=use_cookie),
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
    raw_creator_name = input("Enter creator boosty link or user name > ")
    parsed_creator_name = parse_creator_name(raw_creator_name)
    use_cookie_in = parse_bool(input("Use cookie for download? (y/n) > "))
    if not conf.ready_to_auth():
        logger.warning("authorization headers unfilled in config, sync without cookie forced.")
        use_cookie_in = False
    print_summary(creator_name=parsed_creator_name, use_cookie=use_cookie_in, sync_dir=str(conf.sync_dir))
    if not parse_bool(input("Proceed? (y/n) > ")):
        logger.info("cancelled by user.")
        raise SyncCancelledExc

    logger.info(f"{parsed_creator_name} > {conf.sync_dir} (auth={use_cookie_in}).")

    if not os.path.isdir(conf.sync_dir):
        logger.critical(f"path {conf.sync_dir} is not exists. create it and try again.")
        raise ConfigMalformedExc

    logger.info(f"starting sync media...")
    await fetch_and_save(parsed_creator_name, use_cookie_in)
    await get_profile_stat(parsed_creator_name)
    stat_tracker.show_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[{e.__class__.__name__}] App stopped")
    finally:
        input("Press enter to exit...")
