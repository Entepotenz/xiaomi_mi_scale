#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
if [[ "${TRACE-0}" == "1" ]]; then set -o xtrace; fi

DOCKER_IMAGE="python:3.9.19-slim@sha256:d3185e5aa645a4ff0b52416af05c8465d93791e49c5a0d0f565c119099f26cde"

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
