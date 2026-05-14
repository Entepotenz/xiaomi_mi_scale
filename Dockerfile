FROM docker.io/library/python:3.14.4-slim@sha256:2ca02f32b4d9d893863367ce07ec1972819f476dd38d8612f2a9cb6a41cbb727 AS builder

WORKDIR /app

ENV POETRY_VERSION=1.4.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN pip install --no-cache-dir \
    poetry==${POETRY_VERSION}

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

COPY pyproject.toml poetry.lock ./

RUN poetry install \
    --without dev --no-root

FROM docker.io/library/python:3.14.4-slim@sha256:2ca02f32b4d9d893863367ce07ec1972819f476dd38d8612f2a9cb6a41cbb727

WORKDIR /app

ENV DEBUG=False \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY src ./

ENTRYPOINT ["python3", "-u", "/app/Xiaomi_Scale.py"]
