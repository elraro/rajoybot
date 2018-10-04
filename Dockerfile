FROM python:3.6-alpine

COPY requirements.txt /
RUN apk update \
    && apk add --virtual build-dependencies \
        build-base \
        gcc \
        wget \
        git \
        libffi-dev \
        openssl-dev \
    && pip3 install -r requirements.txt \
    && apk del build-dependencies \
        build-base \
        gcc \
        wget \
        git \
        libffi-dev \
        openssl-dev \
    && rm -rf /var/cache/apk/*

WORKDIR /app
VOLUME /data

ENV SQLITE_FILE=/data/db.sqlite
ENV DATA_JSON=/app/data.json

ADD app /app

ENTRYPOINT ["python3", "bot.py"]
