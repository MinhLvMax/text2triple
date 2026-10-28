from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import logging

from dotenv import load_dotenv


def get_logger(name: str, path, enable_console=True) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)-8s - %(pathname)s:%(funcName)s:%(lineno)d %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    if enable_console:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)

    file = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file.setFormatter(formatter)

    logger.addHandler(file)

    return logger

class Config:
    PROJECT_DIR = Path(__file__).resolve().parents[1]

    DATA_DIR = PROJECT_DIR / 'data'
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    ENV_PATH = PROJECT_DIR / '.env'
    # if not ENV_PATH.exists():
    #     ENV_PATH.write_text(
    #         data='''HISTORY_PDF_DIR=''',
    #         encoding='utf-8'
    #     )

    load_dotenv()
    OPEN_API_KEY=os.getenv('OPEN_API_KEY')
