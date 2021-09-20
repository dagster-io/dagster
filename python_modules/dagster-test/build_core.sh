#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
BASE_DIR="${ROOT}/python_modules/dagster-test/"

function cleanup {
    rm -rf "${BASE_DIR}/modules"
    set +ux
    shopt -u expand_aliases
}

cleanup

# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR


if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image tag.\n" 1>&2
    echo "Usage: ./build.sh 3.7.4 dagster-test-image" 1>&2
    exit 1
fi
set -ux
shopt -s expand_aliases

# e.g. 3.7.4
PYTHON_VERSION=$1

# e.g. dagster-core-test-image
IMAGE_TAG=$2

pushd $BASE_DIR

mkdir -p modules

echo -e "--- \033[32m:truck: Copying files...\033[0m"
alias copy_py="rsync -av \
      --progress \
      --exclude *.egginfo \
      --exclude *.tox \
      --exclude dist \
      --exclude __pycache__ \
      --exclude *.pyc \
      --exclude .coverage"

copy_py $ROOT/python_modules/dagster \
        modules/

PYTHON_SLIM_IMAGE="python:${PYTHON_VERSION}-slim"
BASE_IMAGE=${BASE_IMAGE:=$PYTHON_SLIM_IMAGE}

echo -e "--- \033[32m:docker: Building Docker image\033[0m"
docker build . \
    -f Dockerfile.core \
    --build-arg PYTHON_VERSION="${PYTHON_VERSION}" \
    --build-arg BASE_IMAGE="${BASE_IMAGE}" \
    -t "${IMAGE_TAG}"
