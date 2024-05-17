FROM docker.io/library/python:3.12.3-slim@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63 as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.12.3-slim@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63

ENV DEBUG False

# RUN apt-get update && apt-get install --no-install-recommends -y \
#     bluez \
#     && \
#     rm -rf /var/lib/apt/lists/*

WORKDIR /usr/app/
COPY --from=build /usr/app/venv ./venv
COPY src .
ENV PATH="/usr/app/venv/bin:$PATH"

COPY dockerscripts/ /
RUN chmod +x /entrypoint.sh \
    && chmod +x /cmd.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
