import sys
from pathlib import Path
from typing import Optional

from yaml import load as yamload, FullLoader

from core.logger import logger


class Config:
    __cfg_path: Optional[Path]
    cookie: str
    authorization: str
    sync_dir: Path

    def __init__(self, cfg_path: Path):
        self.__cfg_path = cfg_path
        self.__load()

    def __load(self):
        try:
            with open(self.__cfg_path, "r") as file:
                data = yamload(file, FullLoader)
            auth_conf = data["auth"]
            file_conf = data["file"]
        except Exception as e:
            logger.fatal(f"Config not found or malformed, stopping... detail: {e}")
            sys.exit(1)
        self.cookie = auth_conf.get("cookie")
        self.authorization = auth_conf.get("authorization")
        self.sync_dir = Path(file_conf.get("sync_dir"))

    def ready_to_auth(self) -> bool:
        if self.cookie is None or self.authorization is None:
            return False
        return True


conf = Config(
    Path(r"./config.yml")
)

