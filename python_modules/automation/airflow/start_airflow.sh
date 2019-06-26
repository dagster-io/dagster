#!/bin/bash

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/python_modules/automation/airflow/

brew services start mysql

airflow webserver -D
airflow scheduler -D
airflow worker -D
