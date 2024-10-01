import os
import re
from pathlib import Path

import aiofiles

from boosty.api import download_file
from core.defs import AsciiCommands
from core.logger import logger


def create_dir_if_not_exists(path: Path):
    if not os.path.isdir(path):
        logger.info(f"create directory: {path}")
        os.mkdir(path)


async def download_file_if_not_exists(url: str, path: Path):
    if os.path.isfile(path):
        logger.debug(f"pass saving file {path}: already exists")
        return False
    logger.info(f"will save file: {path}")
    result = await download_file(url, path)
    return result


async def create_text_document(path: Path, content: str, name: str = "contents"):
    to_write = path / (name + ".txt")
    async with aiofiles.open(to_write, "w", encoding="utf-8") as file:
        await file.write(content)


def parse_creator_name(raw_input: str) -> str:
    search = re.search(r"^.*?(boosty\.to/(.*?)/?)$", raw_input)
    if search is None:
        return raw_input
    return search.group(2)


def parse_bool(raw_input: str) -> bool:
    clear_input = raw_input.replace(" ", "")
    clear_input = clear_input.lower()
    match clear_input:
        case "y":
            return True
        case "yes":
            return True
        case "1":
            return True
        case "t":
            return True
        case "true":
            return True
        case _:
            return False


def print_colorized(prefix: str, data: str, warn: bool = False):
    print(prefix, end=": ")
    print(AsciiCommands.COLORIZE_WARN.value if warn else AsciiCommands.COLORIZE_HIGHLIGHT.value, end="")
    print(data, end=AsciiCommands.COLORIZE_DEFAULT.value)


def print_summary(
    creator_name: str,
    use_cookie: bool,
    sync_dir: str,
    download_timeout: int,
    need_load_video: bool,
    need_load_photo: bool,
    need_load_audio: bool,
    storage_type: str,
):
    print_colorized("Sync media for", creator_name)
    if use_cookie:
        print_colorized("Auth policy", "with cookie")
    else:
        print_colorized("Sync media", "WITHOUT cookie", warn=True)
    print_colorized("Sync in", sync_dir)
    print_colorized("Download timeout", f"{download_timeout // 60} min.")
    print_colorized("Photo download", "yes" if need_load_photo else "no", warn=not need_load_photo)
    print_colorized("Video download", "yes" if need_load_video else "no", warn=not need_load_video)
    print_colorized("Audio download", "yes" if need_load_audio else "no")
    print_colorized("Storage type", storage_type)
