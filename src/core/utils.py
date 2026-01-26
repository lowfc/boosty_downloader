import logging
import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse

import flet as ft

from core.defs.common import PostInfo


logger = logging.getLogger(__name__)

post_link_re = re.compile(r'https://boosty\.to/(.*)/posts/([a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12})', re.I)


def parse_post_link(post_link: str) -> Optional[PostInfo]:
    try:
        parsed_url = urlparse(post_link)
        clean_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            '',
            '',
            ''
        ))
    except Exception as e:
        logger.error(f"Error parsing post link: '{post_link}'", exc_info=e)
        return None
    result = post_link_re.match(clean_url)
    if result:
        return PostInfo(
            author=result.group(1),
            id=result.group(2)
        )
    return None


async def get_destination_folder():
    download_folder = await ft.SharedPreferences().get("download-folder")
    if not download_folder:
        try:
            downloads_path = os.path.join(os.environ['USERPROFILE'], 'Downloads')
            if downloads_path:
                return str(downloads_path)
        except Exception as e:
            logger.error("Failed get downloads folder", exc_info=e)
        return r"C:\boosty_dumps"
    return download_folder


def validate_windows_dir_name(dir_name: str) -> "str | None":
    """
    Проверяет и исправляет имя директории для Windows.
    Возвращает корректное имя директории.
    """
    illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'

    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    clean_name = re.sub(illegal_chars, '_', dir_name)

    clean_name = clean_name.strip(' .')

    base_name = Path(clean_name).stem.upper()
    if base_name in reserved_names:
        clean_name = f"_{clean_name}_post"

    if not clean_name:
        return None

    clean_name = clean_name[:255]

    return clean_name