#!/usr/bin/env bash

set -o errexit
set -o pipefail
set -o nounset
if [[ "${TRACE-0}" == "1" ]]; then set -o xtrace; fi

DOCKER_IMAGE="python:3.14.4-slim@sha256:c11aee3b3cae066f55d1e9318fc812673aa6557073b0db0d792b59491b262e0c"

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
