import os
import re
from pathlib import Path
from typing import Optional

import aiofiles

from core.defs import AsciiCommands
from core.logger import logger


def create_dir_if_not_exists(path: Path):
    if not os.path.isdir(path):
        logger.info(f"create directory: {path}")
        os.mkdir(path)


async def create_text_document(path: Path, content: str, ext: str = "txt", name: str = "contents"):
    to_write = path / (name + "." + ext)
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


def print_colorized(prefix: str, data: str, warn: bool = False, end="\n"):
    if prefix:
        print(prefix, end=": ")
    print(AsciiCommands.COLORIZE_WARN.value if warn else AsciiCommands.COLORIZE_HIGHLIGHT.value, end="")
    print(data, end=(AsciiCommands.COLORIZE_DEFAULT.value + end))


def print_summary(
    creator_name: str,
    use_cookie: bool,
    sync_dir: str,
    need_load_video: bool,
    need_load_photo: bool,
    need_load_audio: bool,
    need_load_files: bool,
    storage_type: str,
):
    print("Ok, working with", end=" ")
    print_colorized("", creator_name, end=", ")
    print("home directory:", end=" ")
    print_colorized("", sync_dir, end=" ")
    print("sync type:", end=" ")
    print_colorized("", storage_type)
    print_colorized("Authorization", "enabled" if use_cookie else "disabled", warn=not use_cookie)
    print("photo:", end=" ")
    print_colorized("", "yes" if need_load_photo else "no", warn=not need_load_photo, end=" | ")
    print("video:", end=" ")
    print_colorized("", "yes" if need_load_video else "no", warn=not need_load_video, end=" | ")
    print("audio:", end=" ")
    print_colorized("", "yes" if need_load_audio else "no", warn=not need_load_audio, end=" | ")
    print("files:", end=" ")
    print_colorized("", "yes" if need_load_files else "no", warn=not need_load_files)


def parse_offset_time(offset: str) -> Optional[int]:
    if not offset:
        return None
    try:
        parts = offset.split(":")
        return int(parts[0])
    except Exception as e:
        logger.error(f"Failed parse offset {offset}", exc_info=e)
        return None
