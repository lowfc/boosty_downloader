from pathlib import Path


class Config:  # noqa

    cookie: str = '<you cookie here>'
    authorization: str = "Bearer <token from browser net tools>"
    creator_name: str = "<you creater name here>"
    sync_dir: Path = Path(r"C:\boosty_dumps")


conf = Config()
