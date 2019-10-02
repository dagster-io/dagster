#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the
# test_project directory as pwd.
# The filesystem manipulation below is to support installing local development
# versions of dagster-graphql and dagster.

set -eux

function cleanup {
    rm -rf dagster
    rm -rf dagster-graphql
    rm -rf dagster-aws
    rm -rf dagster-cron
}
# ensure cleanup happens on error or normal exit
trap cleanup EXIT

cp -R ../../../dagster .
cp -R ../../../dagster-graphql .
cp -R ../../../libraries/dagster-aws .
cp -R ../../../libraries/dagster-cron .

rm -rf \
  dagster/*.egg-info \
  dagster/.tox \
  dagster/build \
  dagster/dist \
  dagster-graphql/*.egg-info \
  dagster-graphql/.tox \
  dagster-graphql/build \
  dagster-graphql/dist \
  dagster-cron/*.egg-info \
  dagster-cron/.tox \
  dagster-cron/build \
  dagster-cron/dist \
  dagster-aws/*.egg-info \
  dagster-aws/.tox \
  dagster-aws/build \
  dagster-aws/dist || true

docker build -t dagster-airflow-demo .
