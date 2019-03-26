#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the airline-demo directory as pwd
# Builds the Docker image for Airflow and scaffolds the DAGs

pip install --upgrade pip

cp -R ../dagster . && \
cp -R ../dagit . && \
cp -R ../dagstermill . && \
\
rm -rf dagster/.tox && \
rm -rf dagit/.tox && \
rm -rf dagstermill/.tox && \
\
rm -rf dagster/dist && \
rm -rf dagit/dist && \
rm -rf dagstermill/dist && \
\
rm -rf .tox dist && \
\
docker build -t airline-demo-airflow . && \
docker tag airline-demo-airflow dagster/airline-demo-airflow && \
\
docker build -f Dockerfile-test -t airline-demo-airflow-test . && \
docker tag airline-demo-airflow-test dagster/airline-demo-airflow-test

rm -rf dagster && \
rm -rf dagit && \
rm -rf dagstermill 
