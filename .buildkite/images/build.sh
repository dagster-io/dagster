#! /bin/bash

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/.buildkite/images/integration/

function cleanup {
    rm -rf scala_modules
}

# ensure cleanup happens on error or normal exit
trap cleanup EXIT

cp -R $ROOT/scala_modules .

docker build . --build-arg PYTHON_VERSION=3.7.3 --build-arg PYTHON_MAJOR_VERSION=3 -t dagster/buildkite-integration:py3.7.3-v4
docker push dagster/buildkite-integration:py3.7.3-v4

docker build . --build-arg PYTHON_VERSION=3.6.8 --build-arg PYTHON_MAJOR_VERSION=3 -t dagster/buildkite-integration:py3.6.8-v4
docker push dagster/buildkite-integration:py3.6.8-v4

docker build . --build-arg PYTHON_VERSION=3.5.7 --build-arg PYTHON_MAJOR_VERSION=3 -t dagster/buildkite-integration:py3.5.7-v4
docker push dagster/buildkite-integration:py3.5.7-v4

docker build . --build-arg PYTHON_VERSION=2.7.16 --build-arg PYTHON_MAJOR_VERSION=2 -t dagster/buildkite-integration:py2.7.16-v4
docker push dagster/buildkite-integration:py2.7.16-v4
