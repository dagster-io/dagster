#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the
# test_project directory as pwd.
# The filesystem manipulation below is to support installing local development
# versions of dagit and dagster.

cp -R ../../../dagster . && \
cp -R ../../../dagster-graphql . && \
cp -R ../../../dagit . && \
\
rm -rf dagster/.tox dagster-graphql/.tox dagit/.tox dagster/dist dagster-graphql/dist \
    dagit/dist dagster/*.egg-info dagster-graphql/*.egg-info dagit/*.egg-info dagster/build \
    dagster-graphql/build dagit/build && \
\
docker build -t dagster-airflow-demo . && \
\
rm -rf dagster dagster-graphql dagit
