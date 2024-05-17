FROM docker.io/library/python:3.9.19-slim@sha256:44122e46edb1c3ae2a144778db3e01c78b6de3af20ddcc38d43032decffb00cf as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.9.19-slim@sha256:44122e46edb1c3ae2a144778db3e01c78b6de3af20ddcc38d43032decffb00cf

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
