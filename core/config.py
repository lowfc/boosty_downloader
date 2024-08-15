from pathlib import Path
from typing import Optional, List
from argparse import ArgumentParser

from yaml import load as yamload, FullLoader

from core.logger import logger


class Config:
    __cfg_path: Optional[Path]
    __arg_parser: "ArgumentParser"

    cookie: str
    authorization: str

    sync_dir: Path
    download_chunk_size: int
    download_timeout: int
    max_download_parallel: int

    need_load_photo: bool
    need_load_video: bool

    def __init__(self):
        self.__arg_parser = ArgumentParser(prog='BoostyDownloader', description='Sync media with boosty.to')
        self.__arg_parser.add_argument('-c', '--config')
        self.__load()

    def __load(self):
        args = self.__arg_parser.parse_args()
        self.__cfg_path = Path(args.config or r'.\config.yml')
        try:
            with open(self.__cfg_path, "r") as file:
                data = yamload(file, FullLoader)
            auth_conf = data["auth"]
            file_conf = data["file"]
            content_conf = data["content"]
        except Exception as e:
            logger.fatal(f"Config not found or malformed: {e}")
            raise e
        self.cookie = auth_conf.get("cookie")
        self.authorization = auth_conf.get("authorization")
        self.sync_dir = Path(file_conf.get("sync_dir"))
        self.download_chunk_size = int(file_conf.get("download_chunk_size", 153600))
        self.download_timeout = int(file_conf.get("download_timeout", 3600))
        self.max_download_parallel = int(file_conf.get("max_download_parallel", 5))
        self.need_load_photo = True
        self.need_load_video = True
        collect: Optional[List[str]] = content_conf.get("collect")
        if collect:
            self.need_load_photo = "photos" in collect
            self.need_load_video = "videos" in collect

    def ready_to_auth(self) -> bool:
        if self.cookie is None or self.authorization is None:
            return False
        return True


conf = Config()

