import logging
from datetime import datetime

from core.config import conf

logger = logging.getLogger("boosty_downloader")
logger.setLevel(logging.INFO)

stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

if conf.save_logs_to_file:
    filename = f"boosty_downloader_{datetime.timestamp(datetime.now())}_launch.log"
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
