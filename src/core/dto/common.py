from dataclasses import dataclass


@dataclass
class PostInfo:
    author: str
    id: str

    def generate_url(self) -> str:
        return f"https://boosty.to/{self.author}/posts/{self.id}"
