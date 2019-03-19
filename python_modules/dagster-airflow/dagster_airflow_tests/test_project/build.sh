#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the
# test_project directory as pwd.
# The filesystem manipulation below is to support installing local development
# versions of dagit and dagster.

cp -R ../../../dagster . && \
cp -R ../../../dagit . && \
\
rm -rf dagster/.tox dagit/.tox dagster/dist dagit/dist dagster/*.egg-info \
    dagit/*.egg-info dagster/build dagit/build && \
\
docker build -t dagster-airflow-demo .

rm -rf dagster dagit
