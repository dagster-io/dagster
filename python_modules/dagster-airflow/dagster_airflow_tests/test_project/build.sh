#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the
# test_project directory as pwd.
# The filesystem manipulation below is to support installing local development
# versions of dagster-graphql and dagster.

set -eux

function cleanup {
    rm -rf dagster
    rm -rf dagster-graphql
}
# ensure cleanup happens on error or normal exit
trap cleanup EXIT

cp -R ../../../dagster .
cp -R ../../../dagster-graphql .

rm -rf dagster/.tox dagster-graphql/.tox dagster/dist dagster-graphql/dist \
    dagster/*.egg-info dagster-graphql/*.egg-info dagster/build \
    dagster-graphql/build

docker build -t dagster-airflow-demo .