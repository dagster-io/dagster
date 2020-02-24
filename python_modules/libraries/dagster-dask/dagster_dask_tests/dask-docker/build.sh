#! /bin/bash

# For the avoidance of doubt, this script is meant to be run from within a checkout of the
# dagster repo

# The filesystem manipulation below is to support installing local development
# versions of dagster-graphql, dagster-aws, dagster-dask, and dagster.

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/python_modules/libraries/dagster-dask/dagster_dask_tests/dask-docker/

function cleanup {
    rm -rf dagster
    rm -rf dagster-graphql
    rm -rf dagster-dask
    rm -rf dagster-aws
    rm -rf dagster-cron
    rm -rf examples
}
# ensure cleanup happens on error or normal exit
trap cleanup EXIT

cp -R ../../../../dagster .
cp -R ../../../../dagster-graphql .
rsync -av --progress ../../../dagster-dask . --exclude dagster_dask_tests
cp -R ../../../dagster-aws .
cp -R ../../../dagster-cron .
cp -R ../../../../../examples .


rm -rf \
  dagster/*.egg-info \
  dagster/.tox \
  dagster/build \
  dagster/dist \
  dagster-graphql/*.egg-info \
  dagster-graphql/.tox \
  dagster-graphql/build \
  dagster-graphql/dist \
  dagster-dask/*.egg-info \
  dagster-dask/.tox \
  dagster-dask/build \
  dagster-dask/dist \
  dagster-cron/*.egg-info \
  dagster-cron/.tox \
  dagster-cron/build \
  dagster-cron/dist \
  dagster-aws/*.egg-info \
  dagster-aws/.tox \
  dagster-aws/build \
  dagster-aws/dist || true

docker build . --build-arg PYTHON_VERSION=$1 -t dagster-dask-test:py$1
