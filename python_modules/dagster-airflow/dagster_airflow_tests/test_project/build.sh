#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the
# test_project directory as pwd.
# The filesystem manipulation below is to support installing local development
# versions of dagster-graphql and dagster.

set -ux

function cleanup {
    rm -rf dagster
    rm -rf dagster-graphql
    rm -rf dagster-aws
    rm -rf dagster-cron
    rm -rf dagster-gcp
    rm -rf dagster-airflow
    rm -rf gac.json
    rm -rf examples
    set +ux
}
# # ensure cleanup happens on error or normal exit
trap cleanup INT TERM EXIT ERR

cp $GOOGLE_APPLICATION_CREDENTIALS ./gac.json

cp -R ../../../dagster . && \
cp -R ../../../dagster-graphql . && \
cp -R ../../../libraries/dagster-aws . && \
cp -R ../../../libraries/dagster-cron . && \
cp -R ../../../libraries/dagster-pandas . && \
cp -R ../../../libraries/dagster-gcp . && \
cp -R ../../../../examples . && \
mkdir -p ./dagster-airflow && \
cp -R ../../../dagster-airflow/setup.py ./dagster-airflow/ && \
cp -R ../../../dagster-airflow/dagster_airflow ./dagster-airflow/ && \
\
rm -rf \
  dagster/*.egg-info \
  dagster/.tox \
  dagster/build \
  dagster/dist \
  dagster-graphql/*.egg-info \
  dagster-graphql/.tox \
  dagster-graphql/build \
  dagster-graphql/dist \
  dagster-airflow/*.egg-info \
  dagster-airflow/.tox \
  dagster-airflow/build \
  dagster-airflow/dist \
  dagster-cron/*.egg-info \
  dagster-cron/.tox \
  dagster-cron/build \
  dagster-cron/dist \
  dagster-aws/*.egg-info \
  dagster-aws/.tox \
  dagster-aws/build \
  dagster-aws/dist \
  dagster-pandas/*.egg-info \
  dagster-pandas/.tox \
  dagster-pandas/build \
  dagster-pandas/dist \
  dagster-gcp/*.egg-info \
  dagster-gcp/.tox \
  dagster-gcp/build \
  dagster-gcp/dist \
  examples/*.egg-info \
  examples/.tox \
  examples/build \
  examples/dist && \
\
docker build -t dagster-airflow-demo . && \
docker build -t dagster-airflow-webserver -f Dockerfile-airflow-webserver .

rm -rf dagster
rm -rf dagster-graphql
rm -rf dagster-aws
rm -rf dagster-cron
rm -rf dagster-pandas
rm -rf dagster-gcp
rm -rf dagster-airflow
rm -rf examples
rm -rf gac.json

set +ux
