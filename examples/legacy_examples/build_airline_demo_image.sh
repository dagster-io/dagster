#!/bin/bash

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/examples/legacy_examples

pip install --upgrade pip

# dagster-pandas required. See https://github.com/dagster-io/dagster/issues/1485

function cleanup {
    rm -rf dagster
    rm -rf dagster-graphql
    rm -rf dagster-pandas
    rm -rf dagstermill
    rm -rf dagster-aws
    rm -rf dagster-spark
    rm -rf dagster-pyspark
    rm -rf dagster-postgres
    rm -rf dagster-cron
}
# ensure cleanup happens on error or normal exit
trap cleanup EXIT

cp -R ../../python_modules/dagster .
cp -R ../../python_modules/dagster-graphql .
cp -R ../../python_modules/libraries/dagster-pandas .
cp -R ../../python_modules/libraries/dagstermill .
cp -R ../../python_modules/libraries/dagster-aws .
cp -R ../../python_modules/libraries/dagster-spark .
cp -R ../../python_modules/libraries/dagster-pyspark .
cp -R ../../python_modules/libraries/dagster-postgres .
cp -R ../../python_modules/libraries/dagster-cron .

rm -rf dagster/.tox
rm -rf dagster-graphql/.tox
rm -rf dagster-pandas/.tox
rm -rf dagstermill/.tox
rm -rf dagster-aws/.tox
rm -rf dagster-spark/.tox
rm -rf dagster-pyspark/.tox
rm -rf dagster-postgres/.tox
rm -rf dagster-cron/.tox

rm -rf dagster/dist
rm -rf dagster-graphql/dist
rm -rf dagster-pandas/dist
rm -rf dagstermill/dist
rm -rf dagster-aws/dist
rm -rf dagster-spark/dist
rm -rf dagster-pyspark/dist
rm -rf dagster-postgres/dist
rm -rf dagster-cron/dist

rm -rf .tox dist

docker build -t airline-demo-airflow .
docker tag airline-demo-airflow dagster/airline-demo-airflow
