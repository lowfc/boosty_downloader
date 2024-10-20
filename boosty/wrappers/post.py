import json
from typing import List

from boosty.wrappers.media_pool import MediaPool
from core.logger import logger


class Post:
    _id: str
    title: str
    paragraph: List[str]
    media_pool: MediaPool
    tags: dict
    created_at: int
    updated_at: int
    publish_time: int

    _text_content_malformed: bool = False

    def __init__(self, _id: str, title: str, created_at: int, updated_at: int, publish_time: int):
        self._id = _id
        self.title = title
        self.media_pool = MediaPool()
        self.paragraph = []
        self.tags = {}
        self.created_at = created_at
        self.updated_at = updated_at
        self.publish_time = publish_time

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

    def add_tag(self, _id: int, title: str):
        self.tags[_id] = title

    def get_tags_text(self):
        #sort tags by title and then by id
        sorted_tags = sorted(self.tags.items(), key=lambda item:f'{item[1]}{item[0]}')
        return "\n".join([f'{_id}\t{title}' for _id, title in sorted_tags])

    def get_attributes_text(self):
        return "\n".join([
            f'createdAt\t{self.created_at}',
            f'updatedAt\t{self.updated_at}',
            f'publishTime\t{self.publish_time}'])
