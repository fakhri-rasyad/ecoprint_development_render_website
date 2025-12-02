import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_error_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.ERROR)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    # File handler for errors only
    file_handler = RotatingFileHandler(
        f"{LOG_DIR}/error.log",
        maxBytes=2 * 1024 * 1024,
        backupCount=3             
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
