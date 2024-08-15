from enum import Enum

VIDEO_QUALITY = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "full_hd": 3,
    "ultra_hd": 4,
}


class AsciiCommands(str, Enum):
    COLORIZE_DEFAULT: str = '\033[0m\n'
    COLORIZE_WARN: str = '\033[91m'
    COLORIZE_HIGHLIGHT: str = '\033[92m'
