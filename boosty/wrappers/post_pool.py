from typing import Optional, List

from boosty.wrappers.post import Post


class PostPool:
    __posts: dict
    tags: dict

    def __init__(self):
        self.__posts = {}
        self.tags = {}

    @property
    def posts(self) -> List[Post]:
        return list(self.__posts.values())

    def add_post(self, post: Post):
        self.__posts[post.id] = post

    def get_post(self, _id: str) -> Optional[Post]:
        return self.__posts.get(_id)

    def add_tag(self, _id: int, title: str):
        self.tags[_id] = title

    def get_tags_text(self):
        #sort tags by title and then by id
        sorted_tags = sorted(self.tags.items(), key=lambda item:f'{item[1]}{item[0]}')
        return "\n".join([f'{_id}\t{title}' for _id, title in sorted_tags])

