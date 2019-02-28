#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the test_project directory as pwd

cp -R ../../../dagster . && \
cp -R ../../../dagit . && \
\
rm -rf dagster/.tox && \
rm -rf dagit/.tox && \
\
rm -rf dagster/dist && \
rm -rf dagit/dist && \
\
rm -rf dagster/*.egg-info && \
rm -rf dagit/*.egg-info && \
\
rm -rf dagster/build && \
rm -rf dagit/build && \
\
docker build -t dagster-airflow-demo .

rm -rf dagster && \
rm -rf dagit
