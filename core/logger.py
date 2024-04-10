import logging

logger = logging.getLogger("boosty_downloader")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")


handler.setFormatter(formatter)
logger.addHandler(handler)
