import logging
import os
import re
from datetime import timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import flet as ft

from core.defs.common import PostInfo, DownloadingSettingsDto
from core.logger import setup_logger

logger = setup_logger(__name__)

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
                return str(os.path.join(downloads_path, "boosty.to"))
        except Exception as e:
            logger.error("Failed get downloads folder", exc_info=e)
        return r"C:\boosty.to"
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


def sign_url(url: str, qs: str) -> str:
    parsed_url = urlparse(url)
    existing_params = {}
    if parsed_url.query:
        existing_params = dict(parse_qsl(parsed_url.query))

    if qs.startswith('?'):
        qs = qs[1:]
    new_params = dict(parse_qsl(qs))

    for key, value in new_params.items():
        if key not in existing_params:
            existing_params[key] = value

    new_query_string = urlencode(existing_params)
    updated_url = parsed_url._replace(query=new_query_string)

    return updated_url.geturl()


async def get_download_settings() -> DownloadingSettingsDto:
    need_download_photos = await ft.SharedPreferences().get("need-download-photos") == "True"
    if need_download_photos is None:
        need_download_photos = True
    need_download_videos = await ft.SharedPreferences().get("need-download-videos") == "True"
    if need_download_videos is None:
        need_download_videos = True
    need_download_audios = await ft.SharedPreferences().get("need-download-audios") == "True"
    if need_download_audios is None:
        need_download_audios = True
    need_download_files = await ft.SharedPreferences().get("need-download-files") == "True"
    if need_download_files is None:
        need_download_files = True

    chunk_size = int(await ft.SharedPreferences().get("download-chunk-size") or 153600)
    download_timeout = int(await ft.SharedPreferences().get("download-timeout") or 3600)
    preferred_video_size = await ft.SharedPreferences().get("preferred-video-size") or "ultra_hd"
    post_text_format = await ft.SharedPreferences().get("post-text-format") or "raw"
    max_parallelism = int(await ft.SharedPreferences().get("download-max-parallelism") or 5)
    downloads_folder = await get_destination_folder()

    return DownloadingSettingsDto(
        need_download_photos=need_download_photos,
        need_download_videos=need_download_videos,
        need_download_audios=need_download_audios,
        need_download_files=need_download_files,
        chunk_size=chunk_size,
        download_timeout=download_timeout,
        preferred_video_size=preferred_video_size,
        post_text_format=post_text_format,
        downloads_folder=downloads_folder,
        max_parallelism=max_parallelism
    )
