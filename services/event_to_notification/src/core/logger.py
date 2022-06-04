__all__ = ["get_logger"]
import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


def get_logger(logger_name: str, level: Optional[int] = logging.DEBUG) -> logging.Logger:
    log_format = '%(asctime)s %(name)-30s %(levelname)-8s %(message)s'

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    os.makedirs('/var/log/app/', exist_ok=True)
    handler = RotatingFileHandler(
        f'/var/log/app/{logger_name}.log', maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8',
    )
    handler.setFormatter(logging.Formatter(log_format))
    logger.addHandler(handler)

    return logger