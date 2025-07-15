import sys
from pathlib import Path

from core.sync_data import SyncData
from welcome import print_welcome

try:
    import asyncio
    import os.path

    from boosty.api import get_profile_stat
    from core.config import conf
    from core.exceptions import SyncCancelledExc, ConfigMalformedExc
    from core.logger import logger
    from core.utils import parse_creator_name, parse_bool, print_summary, create_dir_if_not_exists, print_colorized
    from core.launchers import fetch_and_save_media, fetch_and_save_posts
    from core.stat_tracker import stat_tracker
except Exception as e:
    print(f"[{e.__class__.__name__}] App stopped ({e})")
    input("Press enter to exit...")
    sys.exit(1)


async def main():
    if conf.storage_type == "media" and conf.desired_post_id:
        if not parse_bool(
                input("--post_id is set, but storage type is media. argument will not be used. continue? (y/n) > ")
        ):
            logger.info("exit due user command")
            raise SyncCancelledExc
    raw_creator_name = input("Enter creator boosty link or user name > ")
    parsed_creator_name = parse_creator_name(raw_creator_name)
    if parsed_creator_name.replace(" ", "") == "":
        logger.critical("Empty creator name, exit")
        raise ConfigMalformedExc
    use_cookie_in = parse_bool(input("Use cookie for download? (y/n) > "))
    if not conf.ready_to_auth():
        logger.warning("authorization headers unfilled in config, sync without cookie forced.")
        use_cookie_in = False
    print_summary(
        creator_name=parsed_creator_name,
        use_cookie=use_cookie_in,
        sync_dir=str(conf.sync_dir),
        download_timeout=conf.download_timeout,
        need_load_video=conf.need_load_video,
        need_load_photo=conf.need_load_photo,
        need_load_audio=conf.need_load_audio,
        need_load_files=conf.need_load_files,
        post_masquerade=conf.enable_post_masquerade,
        sync_offset_save=conf.sync_offset_save,
        video_size_restriction=conf.max_video_file_size,
        storage_type=conf.storage_type,
    )
    if not parse_bool(input("Proceed? (y/n) > ")):
        raise SyncCancelledExc

    if not os.path.isdir(conf.sync_dir):
        logger.critical(f"path {conf.sync_dir} is not exists. create it and try again.")
        raise ConfigMalformedExc

    base_path: Path = conf.sync_dir / parsed_creator_name
    cache_path = base_path / "__cache__"
    sync_data_file_path = cache_path / conf.default_sd_file_name

    create_dir_if_not_exists(base_path)
    create_dir_if_not_exists(cache_path)

    sync_data = None
    if conf.sync_offset_save:
        sync_data = await SyncData.get_or_create_sync_data(sync_data_file_path, parsed_creator_name)

    print_colorized(f"starting sync", conf.storage_type)
    if conf.storage_type == "media":
        image_start_offset = None
        video_start_offset = None
        audio_start_offset = None
        if sync_data:
            rt_photo_offset = await sync_data.get_runtime_photo_offset()
            rt_video_offset = await sync_data.get_runtime_video_offset()
            rt_audio_offset = await sync_data.get_runtime_audio_offset()
            if any((rt_photo_offset, rt_audio_offset, rt_video_offset)):
                print_colorized("Oops", "Seems like your last sync ends unexpected", warn=True)
                if parse_bool(input("Shall we pick up where we left off? (y/n) > ")):
                    if rt_photo_offset:
                        image_start_offset = rt_photo_offset
                    if rt_video_offset:
                        video_start_offset = rt_video_offset
                    if rt_audio_offset:
                        audio_start_offset = rt_audio_offset
        await fetch_and_save_media(
            creator_name=parsed_creator_name,
            use_cookie=use_cookie_in,
            base_path=base_path,
            sync_data=sync_data,
            image_start_offset=image_start_offset,
            audio_start_offset=audio_start_offset,
            video_start_offset=video_start_offset,
        )
    elif conf.storage_type == "post":
        start_offset = None
        rt_posts_offset = await sync_data.get_runtime_posts_offset()
        if sync_data and rt_posts_offset:
            print_colorized("Oops", "Seems like your last sync ends unexpected", warn=True)
            if parse_bool(input("Shall we pick up where we left off? (y/n) > ")):
                start_offset = rt_posts_offset
        await fetch_and_save_posts(
            creator_name=parsed_creator_name,
            use_cookie=use_cookie_in,
            base_path=base_path,
            cache_path=cache_path,
            start_offset=start_offset,
            sync_data=sync_data
        )
    await get_profile_stat(parsed_creator_name)
    stat_tracker.show_summary()


if __name__ == "__main__":
    try:
        print_welcome()
        asyncio.run(main())
    except Exception as e:
        print(f"[{e.__class__.__name__}] App stopped with: {e.__class__.__name__}")
        if conf.debug:
            raise e
    finally:
        input("\nPress enter to exit...")
