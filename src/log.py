import logging
from logging import handlers
from src import config

def get_logger(name: str):
    format = '''%(asctime)s-%(levelname)-8s
        %(pathname)s:%(funcName)s:%(lineno)d
        %(message)s'''

    logging.basicConfig(
        level=logging.DEBUG,
        format=format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                config.LOG_FILES / 'app.log',
                maxBytes=1 * 1024 * 1024,
                backupCount=3,
                encoding='utf-8',
            )
        ],
    )

    return logging.getLogger(name)