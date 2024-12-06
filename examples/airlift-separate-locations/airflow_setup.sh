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

# Create the airflow.cfg file in $AIRFLOW_HOME. We set a super high import timeout so that we can attach a debugger and mess around with the code.
cat <<EOL > $AIRFLOW_HOME/airflow.cfg
[core]
dags_folder = $DAGS_FOLDER
dagbag_import_timeout = 30000
load_examples = False
[api]
auth_backend = airflow.api.auth.backend.basic_auth
[webserver]
expose_config = True

EOL

# call airflow command to create the default user
airflow db migrate && \
airflow users create \
  --username admin \
--password admin \
  --firstname Peter \
  --lastname Parker \
  --role Admin \
  --email spiderman@superhero.org