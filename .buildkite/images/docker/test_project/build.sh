#!/bin/bash

ROOT=$(git rev-parse --show-toplevel)

set -ux

function cleanup {
    rm -rf $ROOT/.buildkite/images/docker/test_project/build_cache
    set +ux
}

export TOX_PY_VERSION=$1
export GOOGLE_APPLICATION_CREDENTIALS="/tmp/gcp-key-elementl-dev.json"
export DAGSTER_DOCKER_IMAGE=${AWS_ACCOUNT_ID}.dkr.ecr.us-west-1.amazonaws.com/dagster-docker-buildkite:${BUILDKITE_BUILD_ID}-${TOX_PY_VERSION}

aws ecr get-login --no-include-email --region us-west-1 | sh
aws s3 cp s3://${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json $GOOGLE_APPLICATION_CREDENTIALS


# ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR

pushd $ROOT/.buildkite/images/docker/test_project

mkdir -p build_cache

cp $GOOGLE_APPLICATION_CREDENTIALS ./build_cache/gac.json

echo -e "--- \033[32m:truck: Copying files...\033[0m"
cp -R $ROOT/python_modules/dagster \
      $ROOT/python_modules/dagit \
      $ROOT/python_modules/dagster-graphql \
      $ROOT/python_modules/libraries/dagster-aws \
      $ROOT/python_modules/libraries/dagster-cron \
      $ROOT/python_modules/libraries/dagster-pandas \
      $ROOT/python_modules/libraries/dagster-postgres \
      $ROOT/python_modules/libraries/dagster-gcp \
      $ROOT/python_modules/libraries/dagster-k8s \
      $ROOT/python_modules/dagster-airflow \
      $ROOT/examples \
      build_cache/

find . \( -name '*.egg-info' -o -name '*.tox' -o -name 'dist' \) | xargs rm -rf

echo -e "--- \033[32m:docker: Building Docker image\033[0m"
docker build -t dagster-docker-buildkite .
docker tag dagster-docker-buildkite $DAGSTER_DOCKER_IMAGE

echo -e "--- \033[32m:docker: Pushing Docker image\033[0m"
docker push $DAGSTER_DOCKER_IMAGE
