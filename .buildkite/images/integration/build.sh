#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
cd $ROOT/.buildkite/images/integration/
set -eux


if [ "$#" -ne 2 ]; then
    echo "Error: Must specify a Python version and image version.\n" 1>&2
    echo "Usage: ./build.sh 3.7.4 v6" 1>&2
    exit 1
fi

# e.g. 3.7.4
PYTHON_VERSION=$1
# e.g. 3
PYTHON_MAJOR_VERSION="${PYTHON_VERSION:0:1}"
# e.g. 37
PYTHON_MAJMIN=`echo "${PYTHON_VERSION:0:3}" | sed 's/\.//'`

# Version of the buildkite integration image
IMAGE_VERSION=$2

function cleanup {
    rm -rf scala_modules
}

# ensure cleanup happens on error or normal exit
trap cleanup EXIT

rsync -av --exclude='*target*' --exclude='*.idea*' --exclude='*.class' $ROOT/scala_modules .

DEBIAN_VERSION="stretch"
if [ $PYTHON_MAJMIN == "38" ]; then
    DEBIAN_VERSION="buster"
fi

# Build the integration image
docker build . \
    --build-arg DEBIAN_VERSION=$DEBIAN_VERSION \
    --build-arg PYTHON_VERSION=$PYTHON_VERSION \
    --build-arg PYTHON_MAJOR_VERSION=$PYTHON_MAJOR_VERSION \
    -t "dagster/buildkite-integration:py${PYTHON_VERSION}-${IMAGE_VERSION}"
