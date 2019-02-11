#! /bin/bash
# For the avoidance of doubt, this script is meant to be run with the test_project directory as pwd

cp -R ../../../dagster .
cp -R ../../../dagit .
docker build -t dagster-airflow-demo .
rm -r dagster
rm -r dagit
