import logging
import os
from src.config import PATH_FOLDER_LOG
from .custom_logger import CustomLogger
from pathlib import Path

LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
}


def get_custom_logger(logger_name, print_console: bool = False):
    logging.setLoggerClass(CustomLogger)  # Set sử dụng class logger bọc tự định nghĩa
    logger = logging.getLogger(logger_name)  # Khai báo logger dựa trên string tên
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Tắt để tránh nó truyền lên add hander và in log 2 lần

    folder_logger_path = Path(PATH_FOLDER_LOG) / (logger_name)
    os.makedirs(folder_logger_path, exist_ok=True)  # Tạo folder con chứa các file log cụ thể của logger này nếu chưa có

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s") # Format hiển thị cho mỗi dòng log

    for name, level in LOG_LEVELS.items():
        debug_path = folder_logger_path / f'{name}.log'
        file_hander = logging.FileHandler(debug_path, encoding="utf-8")
        file_hander.setLevel(level)
        file_hander.setFormatter(formatter)
        logger.addHandler(file_hander)

    if print_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

main_logger  = get_custom_logger('main_logger', print_console=True)

__all__ = ['main_logger']
