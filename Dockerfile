FROM docker.io/library/python:3.14.3-slim@sha256:5e59aae31ff0e87511226be8e2b94d78c58f05216efda3b07dbbed938ec8583b AS builder

WORKDIR /app

ENV POETRY_VERSION=2.3.4 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1

RUN pip install --no-cache-dir \
    poetry==${POETRY_VERSION}

COPY pyproject.toml poetry.lock ./

RUN poetry install \
    --without dev --no-root

FROM docker.io/library/python:3.14.3-slim@sha256:5e59aae31ff0e87511226be8e2b94d78c58f05216efda3b07dbbed938ec8583b

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

ENV DEBUG=False \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY src ./

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python3", "-u", "/app/Xiaomi_Scale.py"]
