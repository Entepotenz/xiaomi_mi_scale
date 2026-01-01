FROM docker.io/library/python:3.14.2-slim@sha256:f7864aa85847985ba72d2dcbcbafd7475354c848e1abbdf84f523a100800ae0b as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.14.2-slim@sha256:f7864aa85847985ba72d2dcbcbafd7475354c848e1abbdf84f523a100800ae0b

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
