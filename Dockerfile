FROM docker.io/library/python:3.13.3-slim@sha256:914bf5c12ea40a97a78b2bff97fbdb766cc36ec903bfb4358faf2b74d73b555b as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.13.3-slim@sha256:914bf5c12ea40a97a78b2bff97fbdb766cc36ec903bfb4358faf2b74d73b555b

ENV DEBUG False

WORKDIR /usr/app/
COPY --from=build /usr/app/venv ./venv
COPY src .
ENV PATH="/usr/app/venv/bin:$PATH"

COPY dockerscripts/ /
RUN chmod +x /entrypoint.sh \
    && chmod +x /cmd.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/cmd.sh"]
