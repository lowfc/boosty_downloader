import json
import time
from dataclasses import dataclass, field
from enum import Enum
from json import JSONDecodeError
from typing import List, Union, Dict
from datetime import datetime


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
class BoostyPostTextDto:
    content: List[Union[BoostyTextDto, BoostyLinkDto]] = field(default_factory=list)

    def __style_text(self, text: str, codes: List[List[int]]):
        result = ""
        ranges = []
        for code in codes:
            ranges.append([code[1], code[1] + code[2], str(code[0])])
        for i, symbol in enumerate(text):
            for code in ranges:
                if i == code[0] or i == code[1]:
                    result += "**"
            result += symbol
        return result

    def get_content(self, title: str, publish_time: int, md: bool = False) -> str:
        result = ""
        if title:
            result += f"# {title}\n" if md else f"{title} \n\n"
        for block in self.content:
            try:
                unmarshal = json.loads(block.content)
            except JSONDecodeError:
                continue
            if not isinstance(unmarshal, list):
                continue
            text, style, codes = unmarshal
            if style != "unstyled":
                continue
            if isinstance(block, BoostyTextDto):
                if md:
                    result += self.__style_text(text, codes)
                else:
                    result += text
            else:
                if md:
                    result += f"[{self.__style_text(text, codes)}]({block.url})"
                else:
                    result += f"{self.__style_text(text, codes)} (link: {block.url})"

        result += "\n\n"
        post_local_time = datetime.fromtimestamp(publish_time - time.timezone)
        fmt_date = post_local_time.strftime('%d.%m.%Y %H:%M')
        if md:
            result += f"---\n\n*Published {fmt_date}*\n"
        else:
            result += f"[Published {fmt_date}]\n"
        return result


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
