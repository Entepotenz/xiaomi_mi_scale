FROM docker.io/library/python:3.12.4-slim@sha256:da2d7af143dab7cd5b0d5a5c9545fe14e67fc24c394fcf1cf15e8ea16cbd8637 as build

WORKDIR /usr/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    bluez \
    libglib2.0-dev

RUN python -m venv /usr/app/venv
ENV PATH="/usr/app/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM docker.io/library/python:3.12.4-slim@sha256:da2d7af143dab7cd5b0d5a5c9545fe14e67fc24c394fcf1cf15e8ea16cbd8637

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
