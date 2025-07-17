import os
from pathlib import Path
from typing import Optional, List, Literal
from argparse import ArgumentParser

from yaml import load as yamload, FullLoader

from core.defs import VIDEO_QUALITY


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
    need_load_audio: bool
    need_load_files: bool
    sync_offset_save: bool
    enable_post_masquerade: bool
    max_video_file_size: int
    debug: bool

    storage_type: Literal["post", "media"]
    desired_post_id: Optional[str]

    save_logs_to_file: bool
    post_text_in_markdown: bool
    save_metadata: bool
    logs_path: Path

    default_sd_file_name: str

    def __init__(self):
        self.__arg_parser = ArgumentParser(prog='BoostyDownloader', description='Sync media with boosty.to')
        self.__arg_parser.add_argument(
            '-c',
            '--config',
            help="Specify a different path to the config"
        )
        self.__arg_parser.add_argument(
            '-p',
            '--post_id',
            help="Specify the id of the only post that needs to be synchronized. "
                 "Available only in post synchronization mode."
        )
        self.__load()

    def __load(self):
        cfg_path = "./config.yml"
        if os.getenv("TESTING") != "1":
            args = self.__arg_parser.parse_args()
            cfg_path = args.config or cfg_path
            self.desired_post_id = args.post_id

        self.__cfg_path = Path(cfg_path)
        try:
            with open(self.__cfg_path, "r", encoding="utf-8") as file:
                data = yamload(file, FullLoader)
            auth_conf = data["auth"]
            file_conf = data["file"]
            content_conf = data["content"]
            logging_conf = data.get("logging", {})
        except Exception as e:
            print(f"FATAL: Config not found or malformed: {e}")
            raise e
        self.cookie = auth_conf.get("cookie")
        self.authorization = auth_conf.get("authorization")
        self.sync_dir = Path(file_conf.get("sync_dir"))
        self.download_chunk_size = int(file_conf.get("download_chunk_size", 153600))
        self.download_timeout = int(file_conf.get("download_timeout", 3600))
        self.max_download_parallel = int(file_conf.get("max_download_parallel", 5))
        self.sync_offset_save = bool(file_conf.get("sync_offset_save", False))
        self.enable_post_masquerade = bool(file_conf.get("enable_post_masquerade", False))
        max_video_file_size = file_conf.get("max_video_file_size", "no_restrict")
        if max_video_file_size not in VIDEO_QUALITY:
            print(f"max_video_file_size MUST BE IN {tuple(VIDEO_QUALITY.keys())}")
        self.max_video_file_size = VIDEO_QUALITY[max_video_file_size]
        self.need_load_photo = True
        self.need_load_video = True
        self.need_load_audio = True
        self.need_load_files = True
        self.storage_type = content_conf.get("storage_type")
        self.post_text_in_markdown = bool(content_conf.get("post_text_in_markdown", True))
        self.save_metadata = bool(content_conf.get("save_metadata", True))
        self.save_logs_to_file = bool(logging_conf.get("enable_file_logging", False))
        self.logs_path = Path(logging_conf.get("logs_path", "./"))
        self.debug = bool(logging_conf.get("debug", False))
        collect: Optional[List[str]] = content_conf.get("collect", "media")
        if collect:
            self.need_load_photo = "photos" in collect
            self.need_load_video = "videos" in collect
            self.need_load_audio = "audios" in collect
            self.need_load_files = "files" in collect
        self.default_sd_file_name = "meta.json"

    def ready_to_auth(self) -> bool:
        if self.cookie is None or self.authorization is None:
            return False
        if len(self.cookie) < 10 or len(self.authorization) < 10:
            return False
        return True


conf = Config()

