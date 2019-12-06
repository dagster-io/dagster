#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/.buildkite/images/docker/
set -eux

# Version of the buildkite image. Update this when you make significant changes to the image.
IMAGE_VERSION="v6"


if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image type.\n" 1>&2
    echo "Usage: ./build.sh 3.7.4 integration" 1>&2
    exit 1
fi

# e.g. 3.7.4
PYTHON_VERSION=$1
# e.g. 3
PYTHON_MAJOR_VERSION="${PYTHON_VERSION:0:1}"
# e.g. 37
PYTHON_MAJMIN=`echo "${PYTHON_VERSION:0:3}" | sed 's/\.//'`

IMAGE_TYPE=$2

function cleanup {
    rm -rf scala_modules
    rm -rf pyarrow-0.15.1.dev403+gfe41a6822-cp38-cp38-linux_x86_64.whl
}

# ensure cleanup happens on error or normal exit
trap cleanup EXIT

rsync -av --exclude='*target*' --exclude='*.idea*' --exclude='*.class' $ROOT/scala_modules .

# pyarrow for Debian Buster
# this was built in a Buster Docker container using the instructions here:
# https://arrow.apache.org/docs/developers/python.html
gsutil cp gs://elementl-deploy-artifacts-9c3ff00/pyarrow-0.15.1.dev403+gfe41a6822-cp38-cp38-linux_x86_64.whl .

DEBIAN_VERSION="stretch"
if [ $PYTHON_MAJMIN == "38" ]; then
    DEBIAN_VERSION="buster"
fi

if [ $IMAGE_TYPE == "integration" ]; then
    # Build the integration image
    docker build . \
        --no-cache \
        --build-arg DEBIAN_VERSION=$DEBIAN_VERSION \
        --build-arg PYTHON_VERSION=$PYTHON_VERSION \
        --build-arg PYTHON_MAJOR_VERSION=$PYTHON_MAJOR_VERSION \
        --target dagster-integration-image \
        -t "dagster/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"
else
    # Build the public image
    docker build . \
        --no-cache \
        --build-arg PYTHON_VERSION=$PYTHON_VERSION \
        --target dagster-public-image \
        -t "dagster/dagster-py${PYTHON_MAJMIN}"
fi
