#!/bin/bash

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/python_modules/automation/airflow/

brew services stop mysql

pgrep airflow | xargs kill
