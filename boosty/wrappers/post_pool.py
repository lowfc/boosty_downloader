from typing import Optional, List

from boosty.wrappers.post import Post
from core.utils import parse_offset_time


class PostPool:
    __posts: dict
    __tags: dict
    _offset: str
    _closed: bool
    _parsed_offset: Optional[int]

    def set_offset(self, offset: str):
        self._offset = offset

    @property
    def offset(self) -> str:
        return self._offset

    @property
    def parsed_offset(self) -> Optional[int]:
        if not self._parsed_offset:
            self._parsed_offset = parse_offset_time(self._offset)
        return self._parsed_offset

    def close(self):
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def __init__(self):
        self.__posts = {}
        self.__tags = {}
        self._offset = ""
        self._closed = False
        self._parsed_offset = None

    def get_posts(self, tag: Optional[str] = None) -> List[Post]:
        if tag:
            if tag not in self.__tags.keys():
                return []
            return list(self.__tags[tag].values())
        return list(self.__posts.values())

    def add_post(self, post: Post, tag: Optional[str] = None):
        if self._closed:
            raise ValueError("Attempt to extend closed post pool")
        self.__posts[post.id] = post
        if tag:
            if tag not in self.__tags.keys():
                self.__tags[tag] = {}
            self.__tags[tag][post.id] = post

    def get_post(self, _id: str, tag: Optional[str] = None) -> Optional[Post]:
        if tag:
            if tag not in self.__tags.keys():
                return None
            return self.__tags[tag].get(_id)
        return self.__posts.get(_id)

