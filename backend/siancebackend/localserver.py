import logging
from logging.handlers import TimedRotatingFileHandler

import time

import fastapi
from fastapi import Depends, FastAPI, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel, parse_obj_as

import urllib.parse
import json

import uvicorn

from siancedb.config import get_config

app = FastAPI()
cfg = get_config()

PDFDIRECTORY = cfg["letters"]["data"]["letters_pdf"]
REFERENTIALS = cfg["letters"]["referentials"]

logger = logging.getLogger("siance-pdf-server")
logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = TimedRotatingFileHandler("siance_pdf_server.log")
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"ApiStatus": "working"}


app.mount("/pdf", StaticFiles(directory=PDFDIRECTORY), name="pdf")
app.mount("/referentials", StaticFiles(directory=REFERENTIALS), name="referentials")


def run():
    uvicorn.run(app, host=cfg["elasticsearch"]["host"], port=80)
