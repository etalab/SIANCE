#!/usr/bin/env python3

import uvicorn
import logging
import time

from logging.handlers import TimedRotatingFileHandler

from . import config
from . import main


def create_timed_rotating_log(path):
    logger = logging.getLogger("siance-api-log")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler = TimedRotatingFileHandler(path, when="d", interval=1, backupCount=10)
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


if __name__ == "__main__":
    cfg = config.get_config()
    create_timed_rotating_log("siance-api.log")
    uvicorn.run(main.app, host=cfg["api"]["host"], port=int(cfg["api"]["port"]))
