from enum import Enum

VIDEO_QUALITY = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "full_hd": 3,
    "ultra_hd": 4,
    "no_restrict": 1000,
}


class AsciiCommands(str, Enum):
    COLORIZE_DEFAULT = '\033[0m\n'
    COLORIZE_WARN = '\033[91m'
    COLORIZE_HIGHLIGHT = '\033[92m'


class ContentType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
