import os
import re
from pathlib import Path

from boosty.api import download_file
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
    await download_file(url, path)
    return True


def parse_creator_name(raw_input: str) -> str:
    search = re.search(r"^.*?(boosty\.to/(.*?)/?)$", raw_input)
    if search is None:
        return raw_input
    return search.group(2)


def parse_bool(raw_input: str) -> bool:
    match raw_input.lower():
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
    print('\033[91m' if warn else '\033[92m', end="")
    print(data, end='\033[0m\n')


def print_summary(
    creator_name: str,
    use_cookie: bool,
    sync_dir: str
):
    print_colorized("Sync media for", creator_name)
    if use_cookie:
        print_colorized("Auth policy", "with cookie")
    else:
        print_colorized("Sync media", "WITHOUT cookie", warn=True)
    print_colorized("Sync in", sync_dir)
