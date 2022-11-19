FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONIOENCODING "UTF-8"

RUN ["mkdir", "app"]

COPY [".", "/app"]

WORKDIR "/app"

RUN ["pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["python", "main.py"]