FROM python:3.11-alpine AS base

WORKDIR /app

RUN apk add --update --no-cache --virtual .tmp-build-deps \
    gcc libc-dev linux-headers postgresql-dev \
    && apk add libffi-dev

RUN pip3 install --upgrade pip setuptools wheel
RUN pip3 install aiohttp
RUN pip3 install poetry

COPY pyproject.toml ./pyproject.toml
COPY poetry.lock ./poetry.lock
RUN poetry install

COPY main.py ./main.py

ENTRYPOINT ["poetry", "run", "python", "/app/main.py"]
