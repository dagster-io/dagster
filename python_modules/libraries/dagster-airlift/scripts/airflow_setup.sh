#!/bin/bash

# Check if the required arguments are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
  echo "Usage: $0 <absolute_path_to_dags_directory> <airflow_home_directory> <airflow_version> [port]"
  exit 1
fi

DAGS_FOLDER=$1
AIRFLOW_HOME_DIR=$2
AIRFLOW_VERSION=$3
# Set default port to 8080 if not provided as fourth argument
PORT=${4:-8080}

# Validate that the provided paths are absolute paths
if [[ "$DAGS_FOLDER" != /* ]] || [[ "$AIRFLOW_HOME_DIR" != /* ]]; then
  echo "Error: Both paths must be absolute paths."
  exit 1
fi

# Validate airflow version
if [[ "$AIRFLOW_VERSION" != "2" ]] && [[ "$AIRFLOW_VERSION" != "3" ]]; then
  echo "Error: Airflow version must be either '2' or '3'."
  exit 1
fi

# Create the airflow.cfg file in the specified AIRFLOW_HOME_DIR
if [[ "$AIRFLOW_VERSION" == "3" ]]; then
cat <<EOL > $AIRFLOW_HOME_DIR/airflow.cfg
[core]
dags_folder = $DAGS_FOLDER
dagbag_import_timeout = 30
load_examples = False
simple_auth_manager_all_admins = True
[api]
auth_backend = airflow.api.auth.backend.basic_auth
[api_auth]
jwt_secret = fake-secret-key
[webserver]
expose_config = True
web_server_port = $PORT

EOL
else
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
fi

# Initialize the database
AIRFLOW_HOME=$AIRFLOW_HOME_DIR airflow db migrate

# Create default user only for Airflow 2
if [[ "$AIRFLOW_VERSION" == "2" ]]; then
  AIRFLOW_HOME=$AIRFLOW_HOME_DIR airflow users create \
    --username admin \
    --password admin \
    --firstname Peter \
    --lastname Parker \
    --role Admin \
    --email spiderman@superhero.org
fi