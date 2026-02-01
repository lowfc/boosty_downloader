import base64
import json
from dataclasses import dataclass
from typing import Optional

from core.logger import setup_logger

logger = setup_logger()


@dataclass
class PostInfo:
    author: str
    id: str

    def generate_url(self) -> str:
        return f"https://boosty.to/{self.author}/posts/{self.id}"


@dataclass
class AuthToken:
    authorization: str
    cookie: str
    expires_in: int

    @staticmethod
    def from_str(data: str) -> Optional['AuthToken']:
        try:
            decoded = base64.b64decode(data)
            result = json.loads(decoded)
            return AuthToken(
                authorization=result['authorization'],
                expires_in=int(result['expires_in'] / 1000),
                cookie=result['full_cookie'],
            )
        except Exception as e:
            logger.error("Failed decode auth token", exc_info=e)


@dataclass
class DownloadingSettingsDto:
    need_download_photos: bool
    need_download_videos: bool
    need_download_audios: bool
    need_download_files: bool
    chunk_size: int
    download_timeout: int
    preferred_video_size: str
    post_text_format: str
    downloads_folder: str
    max_parallelism: int
