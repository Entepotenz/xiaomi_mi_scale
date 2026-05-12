FROM docker.io/library/python:3.9.19-slim@sha256:44122e46edb1c3ae2a144778db3e01c78b6de3af20ddcc38d43032decffb00cf AS builder

WORKDIR /app

RUN pip install poetry==1.4.2

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

COPY pyproject.toml poetry.lock ./

RUN poetry install \
    --without dev --no-root

FROM docker.io/library/python:3.9.19-slim@sha256:44122e46edb1c3ae2a144778db3e01c78b6de3af20ddcc38d43032decffb00cf

WORKDIR /app

ENV DEBUG=False \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY src ./

ENTRYPOINT ["python3", "-u", "/app/Xiaomi_Scale.py"]
