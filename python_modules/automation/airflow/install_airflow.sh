#!/bin/bash

set -eux

ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/python_modules/automation/airflow/

# airflow initdb will go create a random sqlite DB if this isn't set and it doesn't find the
# airflow.cfg file
[ -z "$AIRFLOW_HOME" ] && { echo "AIRFLOW_HOME must be set to use this script"; exit 1; }

brew update

if brew ls --versions mysql > /dev/null; then
  echo "MySQL already installed, skipping"
else
  brew install mysql
fi

if brew ls --versions rabbitmq > /dev/null; then
  echo "rabbitmq already installed, skipping"
else
  brew install rabbitmq
fi


# Migrate MySQL
./reset_airflow_db.sh

pip install mysqlclient "apache-airflow[celery]>=1.10.2"

rabbitmqctl status

# Use Celery executor
sed -i -e "s/^executor.*/executor = CeleryExecutor/" $AIRFLOW_HOME/airflow.cfg

# Use MySQL
sed -i -e "s|^sql_alchemy_conn.*|sql_alchemy_conn = mysql://airflow:airflow@localhost:3306/airflow|" $AIRFLOW_HOME/airflow.cfg

# Use rabbitmq
sed -i -e "s|^broker_url.*|broker_url = amqp://guest:guest@localhost:5672/|" $AIRFLOW_HOME/airflow.cfg

airflow initdb
