FROM python:3.7-stretch

COPY requirements.txt /
RUN apt update
RUN apt install gcc -y
RUN pip3 install -r requirements.txt

WORKDIR /app
VOLUME /data

ENV SQLITE_FILE=/data/db.sqlite
ENV DATA_JSON=/app/data.json

ADD app /app

ENTRYPOINT ["python3", "bot.py"]
