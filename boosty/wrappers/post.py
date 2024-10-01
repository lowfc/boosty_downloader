import json
from typing import List

from boosty.wrappers.media_pool import MediaPool
from core.logger import logger


class Post:
    _id: str
    title: str
    paragraph: List[str]
    media_pool: MediaPool

    _text_content_malformed: bool = False

    def __init__(self, _id: str, title: str):
        self._id = _id
        self.title = title
        self.media_pool = MediaPool()
        self.paragraph = []

    @property
    def id(self) -> str:
        return self._id

    def add_image(self, _id: str, url: str, width: int, height: int):
        self.media_pool.add_image(_id, url, width, height)

    def add_video(self, _id: str, url: str, size_amount: int):
        self.media_pool.add_video(_id, url, size_amount)

    def add_marshaled_paragraph(self, paragraph_text: str):
        try:
            unmarshal = json.loads(paragraph_text)
            if not isinstance(unmarshal, list):
                raise Exception("Unknown paragraph format")
            if unmarshal[0] != "":
                self.paragraph.append(unmarshal[0])
        except Exception as e:
            logger.error("Failed unmarshal paragraph", exc_info=e)
            self._text_content_malformed = True

    def get_contents_text(self):
        result = ""
        if self.title:
            result += self.title + "\n\n"
        if len(self.paragraph):
            result += "\n".join(self.paragraph)
        return result
