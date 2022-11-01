FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING "UTF-8"

RUN ["mkdir", "app"]

COPY ["requirements.txt", "/app"]
COPY ["main.py", "/app"]
COPY ["./common", "/app"]

WORKDIR /app

ENV UTIL_PORT=9118
EXPOSE ${UTIL_PORT}

ENV JACKETT_HOST=9118
EXPOSE ${JACKETT_HOST}

RUN ["pip", "install", "-r", "/requirements.txt"]

RUN python main.py