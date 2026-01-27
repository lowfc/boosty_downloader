from dataclasses import dataclass


@dataclass
class PostInfo:
    author: str
    id: str

    def generate_url(self) -> str:
        return f"https://boosty.to/{self.author}/posts/{self.id}"


@dataclass
class DownloadingSettingsDto:
    need_download_photos: bool
    need_download_videos: bool
    need_download_audios: bool
    need_download_files: bool
    chunk_size: int
    download_timeout: int
    preferred_video_size: str
    post_text_format: str
    downloads_folder: str
    max_parallelism: int
