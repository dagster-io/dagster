#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)
BASE_DIR="${ROOT}/examples/deploy_docker/from_source"

function cleanup {
    rm -rf "${BASE_DIR}/python_modules"
    rm -rf "${BASE_DIR}/js_modules"
    set +ux
}

cleanup

# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR

set -ux

pushd $BASE_DIR

mkdir -p python_modules
mkdir -p python_modules/libraries/
mkdir -p js_modules

echo -e "--- \033[32m:truck: Copying files...\033[0m"
cp -R $ROOT/python_modules/dagster \
      $ROOT/python_modules/dagit \
      $ROOT/python_modules/dagster-graphql \
      python_modules/

cp -R $ROOT/js_modules/dagit \
      js_modules/

cp -R $ROOT/python_modules/libraries/dagster-postgres \
      $ROOT/python_modules/libraries/dagster-docker \
      python_modules/libraries/

find ./python_modules/ \( -name '*.egg-info' -o -name '*.tox' -o -name 'dist' \) | xargs rm -rf

echo -e "--- \033[32m:docker: Building Docker images\033[0m"
docker-compose build
