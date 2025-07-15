import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Self
from asyncio import Lock

import aiofiles

from core.defs import ContentType
from core.logger import logger


class SyncData:
    __path: Path

    _creator_name: str
    _last_sync_utc: Optional[datetime]

    _last_photo_offset: Optional[str]
    _runtime_photo_offset: Optional[str]
    _last_audio_offset: Optional[str]
    _runtime_audio_offset: Optional[str]
    _last_video_offset: Optional[str]
    _runtime_video_offset: Optional[str]

    _last_posts_offset: Optional[str]
    _runtime_posts_offset: Optional[str]

    def __init__(self, path: Path):
        self.__path = path
        self._creator_name = ""
        self._last_sync_utc = None
        self._last_photo_offset = None
        self._runtime_photo_offset = None
        self._last_audio_offset = None
        self._runtime_audio_offset = None
        self._last_video_offset = None
        self._runtime_video_offset = None
        self._last_posts_offset = None
        self._runtime_posts_offset = None
        self._lock = Lock()

    async def save(self):
        async with self._lock:
            async with aiofiles.open(self.__path, "w") as f:
                await f.write(json.dumps(
                    {
                        "creator_name": self._creator_name,
                        "last_sync_utc": self._last_sync_utc.isoformat() if self._last_sync_utc else None,
                        "last_photo_offset": self._last_photo_offset,
                        "runtime_photo_offset": self._runtime_photo_offset,
                        "last_audio_offset": self._last_audio_offset,
                        "runtime_audio_offset": self._runtime_audio_offset,
                        "last_video_offset": self._last_video_offset,
                        "runtime_video_offset": self._runtime_video_offset,
                        "last_posts_offset": self._last_posts_offset,
                        "runtime_posts_offset": self._runtime_posts_offset,
                    }, indent=2)
                )

    async def get_creator_name(self) -> str:
        async with self._lock:
            return self._creator_name

    async def get_last_sync_utc(self) -> Optional[datetime]:
        async with self._lock:
            return self._last_sync_utc

    async def get_last_photo_offset(self) -> Optional[str]:
        async with self._lock:
            return self._last_photo_offset

    async def get_runtime_photo_offset(self) -> Optional[str]:
        async with self._lock:
            return self._runtime_photo_offset

    async def get_last_audio_offset(self) -> Optional[str]:
        async with self._lock:
            return self._last_audio_offset

    async def get_runtime_audio_offset(self) -> Optional[str]:
        async with self._lock:
            return self._runtime_audio_offset

    async def get_last_video_offset(self) -> Optional[str]:
        async with self._lock:
            return self._last_video_offset

    async def get_runtime_video_offset(self) -> Optional[str]:
        async with self._lock:
            return self._runtime_posts_offset

    async def get_last_posts_offset(self) -> Optional[str]:
        async with self._lock:
            return self._last_posts_offset

    async def get_runtime_posts_offset(self) -> Optional[str]:
        async with self._lock:
            return self._runtime_posts_offset

    async def set_creator_name(self, value: str):
        async with self._lock:
            self._creator_name = value

    async def set_last_sync_utc(self, value: Optional[datetime]):
        async with self._lock:
            self._last_sync_utc = value

    async def set_last_photo_offset(self, value: Optional[str]):
        async with self._lock:
            self._last_photo_offset = value

    async def set_runtime_photo_offset(self, value: Optional[str]):
        async with self._lock:
            self._runtime_photo_offset = value

    async def set_last_audio_offset(self, value: Optional[str]):
        async with self._lock:
            self._last_audio_offset = value

    async def set_runtime_audio_offset(self, value: Optional[str]):
        async with self._lock:
            self._runtime_audio_offset = value

    async def set_last_video_offset(self, value: Optional[str]):
        async with self._lock:
            self._last_video_offset = value

    async def set_runtime_video_offset(self, value: Optional[str]):
        async with self._lock:
            self._runtime_video_offset = value

    async def set_last_posts_offset(self, value: Optional[str]):
        async with self._lock:
            self._last_posts_offset = value

    async def set_runtime_posts_offset(self, value: Optional[str]):
        async with self._lock:
            self._runtime_posts_offset = value

    @classmethod
    async def load(cls, path: Path) -> Optional["Self"]:
        sd = SyncData(path=path)
        try:
            async with aiofiles.open(path, "r") as f:
                raw = await f.read()
                obj = json.loads(raw)
                try:
                    if obj["last_sync_utc"]:
                        await sd.set_last_sync_utc(datetime.fromisoformat(obj["last_sync_utc"]))

                    await sd.set_creator_name(obj["creator_name"])
                    await sd.set_last_photo_offset(obj["last_photo_offset"])
                    await sd.set_runtime_photo_offset(obj["runtime_photo_offset"])
                    await sd.set_last_audio_offset(obj["last_audio_offset"])
                    await sd.set_runtime_audio_offset(obj["runtime_audio_offset"])
                    await sd.set_last_video_offset(obj["last_video_offset"])
                    await sd.set_runtime_video_offset(obj["runtime_video_offset"])
                    await sd.set_last_posts_offset(obj["last_posts_offset"])
                    await sd.set_runtime_posts_offset(obj["runtime_posts_offset"])

                except KeyError as e:
                    logger.error(f"Unknown meta file format, failed to parse. Missing key: {e}")
                    return None
        except FileNotFoundError:
            logger.warning(f"Meta file does not exist at {path}")
            return None
        except Exception as e:
            logger.error("Failed to parse meta file", exc_info=e)
            return None
        return sd

    @staticmethod
    async def get_or_create_sync_data(sync_data_target_path: Path, creator_name: str):
        sync_data = await SyncData.load(sync_data_target_path)
        if not sync_data:
            sync_data = SyncData(sync_data_target_path)
            await sync_data.set_creator_name(creator_name)
            await sync_data.save()
            return sync_data
        cur_creator_name = await sync_data.get_creator_name()
        if cur_creator_name != creator_name:
            raise ValueError(f"Inconsistent sync data file: expected {creator_name}, got: {cur_creator_name}")
        return sync_data

    async def get_last_media_offset(self, media_type: ContentType) -> Optional[str]:
        async with self._lock:
            if media_type == ContentType.IMAGE:
                return self._last_photo_offset
            if media_type == ContentType.AUDIO:
                return self._last_audio_offset
            if media_type == ContentType.VIDEO:
                return self._last_video_offset
            logger.warning(f"Trying to use incompatible media type for get_last_media_offset: {media_type}")
            return None

    async def set_last_media_offset(self, media_type: ContentType, offset: Optional[str]):
        async with self._lock:
            if media_type == ContentType.IMAGE:
                self._last_photo_offset = offset
            elif media_type == ContentType.AUDIO:
                self._last_audio_offset = offset
            elif media_type == ContentType.VIDEO:
                self._last_video_offset = offset
            else:
                logger.warning(f"Trying to use incompatible media type for set_last_media_offset: {media_type}")

    async def get_runtime_media_offset(self, media_type: ContentType) -> Optional[str]:
        async with self._lock:
            if media_type == ContentType.IMAGE:
                return self._runtime_photo_offset
            if media_type == ContentType.AUDIO:
                return self._runtime_audio_offset
            if media_type == ContentType.VIDEO:
                return self._runtime_posts_offset
            logger.warning(f"Trying to use incompatible media type for get_runtime_media_offset: {media_type}")
            return None

    async def set_runtime_media_offset(self, media_type: ContentType, offset: Optional[str]):
        async with self._lock:
            if media_type == ContentType.IMAGE:
                self._runtime_photo_offset = offset
            elif media_type == ContentType.AUDIO:
                self._runtime_audio_offset = offset
            elif media_type == ContentType.VIDEO:
                self._runtime_video_offset = offset
            else:
                logger.warning(f"Trying to use incompatible media type for set_runtime_media_offset: {media_type}")
