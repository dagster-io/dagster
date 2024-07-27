#!/bin/bash

# Check if the path argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <absolute_path_to_dags_directory>"
  exit 1
fi

DAGS_FOLDER=$1

# Validate that the provided path is an absolute path
if [[ "$DAGS_FOLDER" != /* ]]; then
  echo "Error: The provided path is not an absolute path."
  exit 1
fi

# Create the airflow.cfg file in $AIRFLOW_HOME
cat <<EOL > $AIRFLOW_HOME/airflow.cfg
[core]
dags_folder = $DAGS_FOLDER
load_examples = False
[api]
auth_backend = airflow.api.auth.backend.basic_auth
[webserver]
expose_config = True

EOL