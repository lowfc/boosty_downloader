import os
from pathlib import Path

from boosty.api import download_file
from core.logger import logger


def create_dir_if_not_exists(path: Path):
    if not os.path.isdir(path):
        logger.info(f"create directory: {path}")
        os.mkdir(path)


async def download_file_if_not_exists(url: str, path: Path):
    if os.path.isfile(path):
        logger.info(f"pass downloading file {path}: already exists")
        return
    logger.info(f"downloading file {path}")
    await download_file(url, path)
