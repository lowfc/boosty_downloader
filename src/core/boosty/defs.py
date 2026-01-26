from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Dict


class BoostyMediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "ok_video"
    TEXT = "text"
    AUDIO = "audio_file"
    LINK = "link"
    FILE = "file"

class BoostyVideoSizesType(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL_HD = "full_hd"
    ULTRA_HD = "ultra_hd"


@dataclass
class BoostyImageDto:
    id: str
    url: str
    width: int
    height: int
    size: int

@dataclass
class BoostyPlayerUrlDto:
    id: str
    url: str
    size: BoostyVideoSizesType

@dataclass
class BoostyVideoDto:
    player_urls: Dict[BoostyVideoSizesType, BoostyPlayerUrlDto] = field(default_factory=dict)

@dataclass
class BoostyTextDto:
    content: str
    modificator: str

@dataclass
class BoostyAudioDto:
    id: str
    url: str
    size: int

@dataclass
class BoostyLinkDto:
    content: str
    url: str

@dataclass
class BoostyFileDto:
    id: str
    url: str
    size: int
    title: str


@dataclass
class BoostyPostDto:
    has_access: bool
    id: str
    title: str
    publish_time: int
    signed_query: str = ""
    media: List[Union[
        BoostyImageDto,
        BoostyVideoDto,
        BoostyTextDto,
        BoostyAudioDto,
        BoostyLinkDto,
        BoostyFileDto
    ]] = field(default_factory=list)
