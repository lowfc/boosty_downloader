from enum import Enum

BOOSTY_API_BASE_URL = "https://api.boosty.to"
DEFAULT_LIMIT = 50
DEFAULT_LIMIT_BY = "media"
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",  # noqa: E501
    "Sec-Ch-Ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}
DOWNLOAD_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",  # noqa: E501
    "Accept-Encoding": "gzip, deflate, br, zstd",
}

class MediaType(str, Enum):
    VIDEO = "ok_video"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio_file"
    LINK = "link"
    FILE = "file"

