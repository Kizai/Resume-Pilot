import logging
import os
from logging.handlers import RotatingFileHandler


def get_logger():
    """
    Create a logger, set formatting, and add a RotatingFileHandler.
    The log file size is limited to 10MB, and backups are created when the size is exceeded.
    :return: a configured logging.Logger object.
    """
    os.makedirs("./logs", exist_ok=True)
    log_path = './logs/run.log'

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(funcName)s %(lineno)d %(message)s',
                                  datefmt="%Y-%m-%d %H:%M:%S")

    # Use RotatingFileHandler with maxBytes and backupCount parameters
    handler = RotatingFileHandler(log_path, mode='a', maxBytes=10 * 1024 * 1024, backupCount=5)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

