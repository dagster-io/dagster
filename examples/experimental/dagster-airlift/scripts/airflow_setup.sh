#!/bin/bash

# Check if the required arguments are provided
if [ -z "$1" ] || [ -z "$2" ]; then
  echo "Usage: $0 <absolute_path_to_dags_directory> <airflow_home_directory> [port]"
  exit 1
fi

DAGS_FOLDER=$1
AIRFLOW_HOME_DIR=$2
# Set default port to 8080 if not provided as third argument
PORT=${3:-8080}

# Validate that the provided paths are absolute paths
if [[ "$DAGS_FOLDER" != /* ]] || [[ "$AIRFLOW_HOME_DIR" != /* ]]; then
  echo "Error: Both paths must be absolute paths."
  exit 1
fi

# Create the airflow.cfg file in the specified AIRFLOW_HOME_DIR
cat <<EOL > $AIRFLOW_HOME_DIR/airflow.cfg
[core]
dags_folder = $DAGS_FOLDER
dagbag_import_timeout = 30
load_examples = False
[api]
auth_backend = airflow.api.auth.backend.basic_auth
[webserver]
expose_config = True
web_server_port = $PORT

EOL

# call airflow command to create the default user
AIRFLOW_HOME=$AIRFLOW_HOME_DIR airflow db migrate && \
AIRFLOW_HOME=$AIRFLOW_HOME_DIR airflow users create \
  --username admin \
  --password admin \
  --firstname Peter \
  --lastname Parker \
  --role Admin \
  --email spiderman@superhero.org