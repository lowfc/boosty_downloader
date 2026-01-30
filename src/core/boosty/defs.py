from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Dict



class BoostyMediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "ok_video"
    AUDIO = "audio_file"
    FILE = "file"
    LINK = "link"
    TEXT = "text"
    LIST = "list"

class BoostyVideoSizesType(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL_HD = "full_hd"
    ULTRA_HD = "ultra_hd"

VIDEO_QUALITY_GRADE = (
    BoostyVideoSizesType.ULTRA_HD.value,
    BoostyVideoSizesType.FULL_HD.value,
    BoostyVideoSizesType.HIGH.value,
    BoostyVideoSizesType.MEDIUM.value,
    BoostyVideoSizesType.LOW.value,
)


@dataclass
class BoostyImageDto:
    id: str
    url: str
    width: int
    height: int
    size: int

@dataclass
class BoostyPlayerUrlDto:
    url: str
    size: BoostyVideoSizesType

@dataclass
class BoostyVideoDto:
    id: str
    title: str
    player_urls: Dict[BoostyVideoSizesType, BoostyPlayerUrlDto] = field(default_factory=dict)

    def get_title(self) -> str:
        return f"{self.title if self.title else self.id}.mp4"


@dataclass
class BoostyAudioDto:
    id: str
    url: str
    size: int
    title: str

    def get_title(self) -> str:
        return self.title if self.title else f"{self.id}.mp3"

@dataclass
class BoostyFileDto:
    id: str
    url: str
    size: int
    title: str


@dataclass
class BoostyTextDto:
    content: str
    modificator: str

@dataclass
class BoostyLinkDto:
    content: str
    url: str


@dataclass
class BoostyListDto:
    style: str
    items: List[Dict] = field(default_factory=list)

@dataclass
class BoostyPostTextDto:
    content: List[Union[BoostyTextDto, BoostyLinkDto, BoostyListDto]] = field(default_factory=list)


@dataclass
class BoostyPostDto:
    has_access: bool
    id: str
    title: str
    publish_time: int
    signed_query: str = ""
    text_content: BoostyPostTextDto = field(default_factory=BoostyPostTextDto)
    media: List[Union[
        BoostyImageDto,
        BoostyVideoDto,
        BoostyAudioDto,
        BoostyFileDto
    ]] = field(default_factory=list)
