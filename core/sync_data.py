import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Self

from core.logger import logger


class SyncData:
    __path: Path

    creator_name: str
    last_sync_utc: Optional[datetime]

    last_photo_offset: Optional[str]
    last_audio_offset: Optional[str]
    last_video_offset: Optional[str]
    last_posts_offset: Optional[str]

    def __init__(self, path: Path):
        self.__path = path
        self.creator_name = ""
        self.last_sync_utc = None
        self.last_photo_offset = None
        self.last_audio_offset = None
        self.last_video_offset = None
        self.last_posts_offset = None

    def save(self):
        with open(self.__path, "w") as f:
            f.write(json.dumps(
                {
                    "creator_name": self.creator_name,
                    "last_sync_utc": self.last_sync_utc.isoformat() if self.last_sync_utc else None,
                    "last_photo_offset": self.last_photo_offset,
                    "last_audio_offset": self.last_audio_offset,
                    "last_video_offset": self.last_video_offset,
                    "last_posts_offset": self.last_posts_offset,
                }, indent=2)
            )

    @classmethod
    def load(cls, path: Path) -> Optional["Self"]:
        sd = SyncData(path=path)
        try:
            with open(path, "r") as f:
                raw = f.read()
                obj = json.loads(raw)
                try:
                    sd.last_sync_utc = datetime.fromisoformat(obj["last_sync_utc"]) if obj["last_sync_utc"] else None
                    sd.creator_name = obj["creator_name"]
                    sd.last_photo_offset = obj["last_photo_offset"]
                    sd.last_audio_offset = obj["last_audio_offset"]
                    sd.last_video_offset = obj["last_video_offset"]
                    sd.last_posts_offset = obj["last_posts_offset"]
                except KeyError:
                    logger.error("Unknown meta file format, failed parse")
                    return
        except FileNotFoundError:
            logger.warning(f"meta file is not exists at {path}")
            return
        except Exception as e:
            logger.error("Failed parse meta file", exc_info=e)
            return
        return sd
