FROM python:3.8-alpine

EXPOSE 8080

COPY requirements.txt /
RUN pip3 install -r requirements.txt

WORKDIR /app
VOLUME /data

ENV SQLITE_FILE=/data/db.sqlite
ENV DATA_JSON=/app/data.json

ADD app /app

ENTRYPOINT ["python3", "bot.py"]
