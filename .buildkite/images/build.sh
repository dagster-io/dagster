#! /bin/bash

set -eu

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/.buildkite/images/integration/

docker build . --build-arg pyver=3.7.3 -t dagster/buildkite-integration:py3.7.3
docker build . --build-arg pyver=3.6.8 -t dagster/buildkite-integration:py3.6.8
docker build . --build-arg pyver=3.5.7 -t dagster/buildkite-integration:py3.5.7
docker build . --build-arg pyver=2.7.16 -t dagster/buildkite-integration:py2.7.16

docker push dagster/buildkite-integration:py3.7.3
docker push dagster/buildkite-integration:py3.6.8
docker push dagster/buildkite-integration:py3.5.7
docker push dagster/buildkite-integration:py2.7.16
