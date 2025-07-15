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
    need_load_files: bool,
    post_masquerade: bool,
    sync_offset_save: bool,
    video_size_restriction: str,
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
    print_colorized("Audio download", "yes" if need_load_audio else "no", warn=not need_load_audio)
    print_colorized("Files download", "yes" if need_load_files else "no", warn=not need_load_files)
    print_colorized("Save original posts name", "yes" if post_masquerade else "no")
    print_colorized("Save sync offset", "yes" if sync_offset_save else "no", warn=not sync_offset_save)
    mvs = ("not " if video_size_restriction == 1000 else "") + "restricted"
    print_colorized("Max video size", mvs, warn=video_size_restriction != 1000)
    print_colorized("Storage type", storage_type)


def parse_offset_time(offset: str) -> Optional[int]:
    if not offset:
        return
    try:
        parts = offset.split(":")
        return int(parts[0])
    except Exception:
        logger.error(f"Failed parse offset {offset}")
