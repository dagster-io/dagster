#!/bin/bash

# airflow initdb will go create a random sqlite DB if this isn't set and it doesn't find the
# airflow.cfg file
[ -z "$AIRFLOW_HOME" ] && { echo "AIRFLOW_HOME must be set to use this script"; exit 1; }

echo "DROP DATABASE IF EXISTS airflow;" | mysql
echo "CREATE DATABASE airflow CHARACTER SET utf8 COLLATE utf8_unicode_ci;" | mysql
echo "GRANT ALL PRIVILEGES ON * . * TO 'airflow'@'localhost';" | mysql
airflow initdb
