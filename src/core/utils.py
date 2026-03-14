import os
import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import flet as ft

from core.defs.common import PostInfo, DownloadingSettingsDto
from core.logger import setup_logger

logger = setup_logger()

uuid4_re_pattern = "[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"
post_link_re = re.compile(rf'(https://)?boosty\.to/(.*)/posts/({uuid4_re_pattern})', re.I)
author_link_re = re.compile(r'(https://)?boosty\.to/(.*)$', re.I)
image_link_feed_re = re.compile(rf'(https://)?boosty\.to/app/feed/(.*)/posts/{uuid4_re_pattern}/media/({uuid4_re_pattern})', re.I)
image_link_author_feed_re = re.compile(rf'(https://)?boosty\.to/(.*)/blog/media/{uuid4_re_pattern}/({uuid4_re_pattern})', re.I)
image_link_author_post_re = re.compile(rf'(https://)?boosty\.to/(.*)/posts/{uuid4_re_pattern}/media/({uuid4_re_pattern})', re.I)
image_link_direct_message_re = re.compile(rf'(https://)?boosty\.to/app/messages/media/(\d)+/({uuid4_re_pattern})', re.I)


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
            author=result.group(2),
            id=result.group(3)
        )
    return None


def parse_image_link(image_link: str) -> Optional[str]:
    try:
        parsed_url = urlparse(image_link)
        clean_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            '',
            '',
            ''
        ))
        for exp in (image_link_feed_re, image_link_author_feed_re, image_link_author_post_re, image_link_direct_message_re):
            if result := exp.match(clean_url):
                return result.group(3)
        return None
    except Exception as e:
        logger.error(f"Error parsing image link: '{image_link}'", exc_info=e)
        return None


def parse_author_link(author_link: str) -> Optional[str]:
    try:
        result = author_link_re.match(author_link)
        if result:
            return result.group(2)
        return author_link.replace("/", "")
    except Exception as e:
        logger.error(f"Error parsing author link: '{author_link}'", exc_info=e)
        return None


def get_default_downloads_folder(device_info: "ft.DeviceInfo") -> Optional[Path]:
    if isinstance(device_info, ft.WindowsDeviceInfo):
        return Path(f"C:\\Users\\{device_info.user_name}\\Downloads")
    elif isinstance(device_info, ft.LinuxDeviceInfo):
        return Path(f"/home/{device_info.machine_id}/Downloads")
    elif isinstance(device_info, ft.MacDeviceInfo):
        return Path("~/Downloads")
    return None


async def get_destination_folder(device_info: Optional["ft.DeviceInfo"]) -> Optional[str]:
    download_folder = await ft.SharedPreferences().get("download-folder")
    if not download_folder and device_info:
        try:
            return str(get_default_downloads_folder(device_info))
        except Exception as e:
            logger.error("Failed get downloads folder", exc_info=e)
        return None
    return download_folder


def validate_windows_dir_name(dir_name: str) -> str:
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


async def get_download_settings(device_info: Optional["ft.DeviceInfo"]) -> Optional[DownloadingSettingsDto]:
    downloads_folder = await get_destination_folder(device_info)
    if not downloads_folder:
        return None

    need_download_photos = await ft.SharedPreferences().get("need-download-photos")
    if need_download_photos == "True" or need_download_photos is None:
        need_download_photos = True
    else:
        need_download_photos = False

    need_download_videos = await ft.SharedPreferences().get("need-download-videos")
    if need_download_videos == "True" or need_download_videos is None:
        need_download_videos = True
    else:
        need_download_videos = False

    need_download_audios = await ft.SharedPreferences().get("need-download-audios")
    if need_download_audios == "True" or need_download_audios is None:
        need_download_audios = True
    else:
        need_download_audios = False

    need_download_files = await ft.SharedPreferences().get("need-download-files")
    if need_download_files == "True" or need_download_files is None:
        need_download_files = True
    else:
        need_download_files = False

    chunk_size = int(await ft.SharedPreferences().get("download-chunk-size") or 153600)
    if chunk_size < 1500:
        chunk_size = 1500
    elif chunk_size > 500000:
        chunk_size = 500000
    download_timeout = int(await ft.SharedPreferences().get("download-timeout") or 3600)
    if download_timeout < 100:
        download_timeout = 100
    elif download_timeout > 1000000:
        download_timeout = 1000000
    preferred_video_size = await ft.SharedPreferences().get("preferred-video-size") or "ultra_hd"
    post_text_format = await ft.SharedPreferences().get("post-text-format") or "raw"
    max_parallelism = int(await ft.SharedPreferences().get("download-max-parallelism") or 5)
    if max_parallelism < 1:
        max_parallelism = 1
    elif max_parallelism > 30:
        max_parallelism = 30

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
