FROM docker.io/library/python:3.9.19-slim@sha256:69e712dbe4c4a166527cbf69374533125cfb6ee93a5e39031a0191c741d386d7 as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.9.19-slim@sha256:69e712dbe4c4a166527cbf69374533125cfb6ee93a5e39031a0191c741d386d7

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
