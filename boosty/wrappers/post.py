import json
import time
from datetime import datetime
from typing import List, Optional

from boosty.wrappers.media_pool import MediaPool
from core.logger import logger


class Post:
    _id: str
    title: str
    text_blocks: List[str]
    media_pool: MediaPool
    markdown_text: bool
    publish_time: Optional[int]
    _text_content_malformed: bool

    _id_prefix_rel: dict[int, str] = {"0": "**"}

    def __init__(self, _id: str, title: str, markdown_text: bool = False, publish_time: Optional[int] = None):
        self._id = _id
        self.title = title
        self.media_pool = MediaPool()
        self.markdown_text = markdown_text
        self.publish_time = publish_time
        self.text_blocks = []
        self._text_content_malformed = False

    @property
    def id(self) -> str:
        return self._id

    def add_image(self, _id: str, url: str, width: int, height: int):
        self.media_pool.add_image(_id, url, width, height)

    def add_video(self, _id: str, url: str, size_amount: int):
        self.media_pool.add_video(_id, url, size_amount)

    def parse_line_markdown(self, text: str, codes: list) -> str:
        result = ""
        ranges = []
        for code in codes:
            ranges.append([code[1], code[1] + code[2], str(code[0])])
        for i, symbol in enumerate(text):
            for code in ranges:
                if i == code[0] or i == code[1]:
                    result += self._id_prefix_rel.get(code[2], "")
            result += symbol
        return result

    def unmarshal_text(self, text: str) -> Optional[str]:
        try:
            unmarshal = json.loads(text)
            if not isinstance(unmarshal, list):
                raise Exception("Unknown block format")
            if unmarshal[0] == "":
                return
            if self.markdown_text:
                if unmarshal[1] != "unstyled" or not isinstance(unmarshal[2], list):
                    raise Exception(f"Unsupported text type: {unmarshal}")
                return self.parse_line_markdown(unmarshal[0], unmarshal[2])
            else:
                return unmarshal[0]
        except Exception as e:
            logger.error("Failed unmarshal paragraph", exc_info=e)
            return None

    def add_marshaled_text(self, text: str):
        unmarshal = self.unmarshal_text(text)
        if unmarshal:
            self.text_blocks.append(unmarshal)
        else:
            self._text_content_malformed = True

    def add_block_end(self):
        self.text_blocks.append("\n\n")

    def add_link(self, marshaled_text: str, link: str):
        unmarshal = self.unmarshal_text(marshaled_text)
        text = unmarshal if unmarshal else ""
        if self.markdown_text:
            self.text_blocks.append(f"[{text}]({link})")
        else:
            if text:
                self.text_blocks.append(f"{text} (ссылка: {link})")
            else:
                self.text_blocks.append(link)

    def get_contents_text(self):
        result = ""
        if self.title:
            if self.markdown_text:
                result += "# "
            else:
                result += self.title + "\n" + ("-" * len(self.title)) + "\n\n"
        if len(self.text_blocks):
            result += "".join(self.text_blocks)
        if self.publish_time:
            result += "\n\n"
            post_local_time = datetime.fromtimestamp(self.publish_time - time.timezone)
            fmt_date = post_local_time.strftime('%d.%m.%Y %H:%M')
            if self.markdown_text:
                result += f"---\n\n*Опубликовано {fmt_date}*\n"
            else:
                result += f"[Опубликовано {fmt_date}]\n"
        return result
