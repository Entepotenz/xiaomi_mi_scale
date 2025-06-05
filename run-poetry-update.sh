#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
if [[ "${TRACE-0}" == "1" ]]; then set -o xtrace; fi

DOCKER_IMAGE="python:3.13.4-slim@sha256:d97b595c5f4ac718102e5a5a91adaf04b22e852961a698411637c718d45867c8"

docker run --rm \
    --pull always \
    -it \
    -v "$(pwd)/:/source" \
    -v "/source/.venv" \
    $DOCKER_IMAGE bash -c "\
    pip install poetry; \
    cd /source; \
    poetry self add poetry-plugin-export; \
    poetry update; \
    poetry lock; \
    poetry export --format requirements.txt --without dev --output /source/requirements.txt; \
    poetry export --format requirements.txt --with dev --output /source/requirements-dev.txt;"
