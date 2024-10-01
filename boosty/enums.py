from enum import Enum


class MediaType(str, Enum):
    VIDEO = "ok_video"
    IMAGE = "image"
    TEXT = "text"
    AUDIO = "audio_file"
