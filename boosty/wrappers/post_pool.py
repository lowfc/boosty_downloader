from typing import Optional, List

from boosty.wrappers.post import Post


class PostPool:
    __posts: dict

    def __init__(self):
        self.__posts = {}

    @property
    def posts(self) -> List[Post]:
        return list(self.__posts.values())

    def add_post(self, post: Post):
        self.__posts[post.id] = post

    def get_post(self, _id: str) -> Optional[Post]:
        return self.__posts.get(_id)

