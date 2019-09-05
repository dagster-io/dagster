#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/.buildkite/images/docker/
set -eux

# Version of the buildkite image. Update this when you make significant changes to the image.
IMAGE_VERSION="v5"


if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image type.\n" 1>&2
    echo "Usage: ./push.sh 3.7.4 integration" 1>&2
    exit 1
fi

PYTHON_VERSION=$1
PYTHON_MAJOR_VERSION="${PYTHON_VERSION:0:1}"
IMAGE_TYPE=$2

if [ $IMAGE_TYPE == "integration" ]; then
    docker push "dagster/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"
else
    docker push "dagster/dagster:py${PYTHON_VERSION}"
fi
