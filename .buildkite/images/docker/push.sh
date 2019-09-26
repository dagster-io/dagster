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

# e.g. 3.7.4
PYTHON_VERSION=$1
# e.g. 3
PYTHON_MAJOR_VERSION="${PYTHON_VERSION:0:1}"
# e.g. 37
PYTHON_MAJMIN=`echo "${PYTHON_VERSION:0:3}" | sed 's/\.//'`

IMAGE_TYPE=$2

TAG=`date '+%Y-%m-%d'`

if [ $IMAGE_TYPE == "integration" ]; then
    docker tag "dagster/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}" \
        "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"

    docker push "${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"
else
    docker tag "dagster/dagster-py${PYTHON_MAJMIN}" "dagster/dagster-py${PYTHON_MAJMIN}:${TAG}"
    docker tag "dagster/dagster-py${PYTHON_MAJMIN}" "dagster/dagster-py${PYTHON_MAJMIN}:latest"

    docker push "dagster/dagster-py${PYTHON_MAJMIN}:${TAG}"
    docker push "dagster/dagster-py${PYTHON_MAJMIN}:latest"
fi
