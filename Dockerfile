FROM python:3.13-slim

EXPOSE 8080

# Install dependencies first (cached layer)
WORKDIR /build
COPY pyproject.toml .
RUN pip3 install --no-cache-dir .

WORKDIR /app
VOLUME /data

ENV SQLITE_FILE=/data/db.sqlite
ENV DATA_JSON=/app/data.json

COPY app/ /app/

ENTRYPOINT ["python3", "bot.py"]
