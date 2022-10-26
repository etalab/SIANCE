FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

COPY ./requirements.txt /app
RUN pip3 install -r requirements.txt


COPY ./databases /databases
RUN cd /databases && pip3 install .

COPY . /app/app

COPY ./config.json /app/config.json
COPY ./regions.json /siance/data/regions.json

RUN mkdir /app/logs
