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
# pip uninstall -y dagster-airflow && \
pip install -e ../dagster-airflow && \
\
dagster-airflow scaffold airline_demo_download_pipeline --image airline-demo-airflow \
-e environments/local_base.yml -e environments/local_fast_download.yml --install && \
\
dagster-airflow scaffold airline_demo_ingest_pipeline --image airline-demo-airflow \
-e environments/local_base.yml -e environments/local_ingest.yml --install && \
\
dagster-airflow scaffold airline_demo_warehouse_pipeline --image airline-demo-airflow \
-e environments/local_base.yml -e environments/local_warehouse.yml --install

rm -rf dagster && \
rm -rf dagit && \
rm -rf dagstermill 
