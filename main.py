import sys

try:
    import asyncio
    import os.path

    from boosty.api import get_profile_stat
    from core.config import conf
    from core.exceptions import SyncCancelledExc, ConfigMalformedExc
    from core.logger import logger
    from core.utils import parse_creator_name, parse_bool, print_summary
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
        storage_type=conf.storage_type
    )
    if not parse_bool(input("Proceed? (y/n) > ")):
        raise SyncCancelledExc

    logger.info(f"{parsed_creator_name} > {conf.sync_dir} (by {conf.storage_type}) (auth={use_cookie_in}).")

    if not os.path.isdir(conf.sync_dir):
        logger.critical(f"path {conf.sync_dir} is not exists. create it and try again.")
        raise ConfigMalformedExc

    logger.info(f"starting sync {conf.storage_type}...")
    if conf.storage_type == "media":
        await fetch_and_save_media(parsed_creator_name, use_cookie_in)
    elif conf.storage_type == "post":
        await fetch_and_save_posts(parsed_creator_name, use_cookie_in)
    await get_profile_stat(parsed_creator_name)
    stat_tracker.show_summary()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[{e.__class__.__name__}] App stopped")
        raise e
    finally:
        input("\nPress enter to exit...")
