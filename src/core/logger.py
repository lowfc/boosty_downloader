import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(log_file="runtime.log"):
    logger = logging.getLogger("boosty_downloader_logger")

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(asctime)s %(filename)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=50 * 1024 * 1024,
            backupCount=1,
            mode="w",
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Can't create log file: {e}")

    logger.addHandler(console_handler)

    logger.propagate = False

    logger.info(f"Logger created: {log_file}")

    return logger
