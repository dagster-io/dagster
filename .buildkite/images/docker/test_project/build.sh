#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)

function cleanup {
    rm -rf $ROOT/.buildkite/images/docker/test_project/build_cache
    set +ux
}

# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR


if [ "$#" -ne 1 ]; then
    echo "Error: Must specify a Python version.\n" 1>&2
    echo "Usage: ./build.sh 3.7.4" 1>&2
    exit 1
fi
set -ux

# e.g. 3.7.4
PYTHON_VERSION=$1

pushd $ROOT/.buildkite/images/docker/test_project

mkdir -p build_cache

cp $GOOGLE_APPLICATION_CREDENTIALS ./build_cache/gac.json

echo -e "--- \033[32m:truck: Copying files...\033[0m"
cp -R $ROOT/python_modules/dagster \
      $ROOT/python_modules/dagit \
      $ROOT/python_modules/dagster-graphql \
      $ROOT/python_modules/libraries/dagster-airflow \
      $ROOT/python_modules/libraries/dagster-aws \
      $ROOT/python_modules/libraries/dagster-celery \
      $ROOT/python_modules/libraries/dagster-cron \
      $ROOT/python_modules/libraries/dagster-pandas \
      $ROOT/python_modules/libraries/dagster-postgres \
      $ROOT/python_modules/libraries/dagster-gcp \
      $ROOT/python_modules/libraries/dagster-k8s \
      $ROOT/examples \
      build_cache/

find . \( -name '*.egg-info' -o -name '*.tox' -o -name 'dist' \) | xargs rm -rf

echo -e "--- \033[32m:docker: Building Docker image\033[0m"
docker build . \
    --build-arg PYTHON_VERSION=$PYTHON_VERSION \
    -t dagster-docker-buildkite
