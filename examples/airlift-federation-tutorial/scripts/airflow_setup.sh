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

# Generate a unique secret key
SECRET_KEY=$(openssl rand -hex 30)

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
secret_key = $SECRET_KEY

EOL

# Create the webserver_config.py file
cat <<EOL > $AIRFLOW_HOME_DIR/webserver_config.py
# -*- coding: utf-8 -*-
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

import os
from flask_appbuilder.security.manager import AUTH_DB

# from airflow.www.fab_security.manager import AUTH_LDAP

basedir = os.path.abspath(os.path.dirname(__file__))

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'webserver.db')

# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True

# Use a unique cookie name for this instance based on port
SESSION_COOKIE_NAME = "airflow_session_${PORT}"

# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
# For details on how to set up each of the following authentication, see
# http://flask-appbuilder.readthedocs.io/en/latest/security.html

# The authentication type
# AUTH_OID : Is for OpenID
# AUTH_DB : Is for database
# AUTH_LDAP : Is for LDAP
# AUTH_REMOTE_USER : Is for using REMOTE_USER from web server
# AUTH_OAUTH : Is for OAuth
AUTH_TYPE = AUTH_DB

# When using LDAP Auth, setup the ldap server
# LDAP_SERVER = "ldap://ldapserver.new"
# LDAP_PORT = 389
# LDAP_USE_TLS = False
# LDAP_SEARCH_SCOPE = "LEVEL"
# LDAP_BIND_USER = "uid=admin,ou=users,dc=example,dc=com"
# LDAP_BIND_PASSWORD = "admin_password"
# LDAP_BASEDN = "dc=example,dc=com"
# LDAP_USER_DN = "ou=users"
# LDAP_USER_FILTER = "(uid=%s)"
# LDAP_GROUP_DN = "ou=groups"
# LDAP_GROUP_FILTER = "(member=%s)"
# LDAP_USER_NAME_FORMAT = "uid=%s,ou=users,dc=example,dc=com"
# LDAP_GROUP_NAME_FORMAT = "cn=%s,ou=groups,dc=example,dc=com"

# Uncomment to setup Full admin role name
# AUTH_ROLE_ADMIN = 'Admin'

# Uncomment to setup Public role name, no authentication needed
# AUTH_ROLE_PUBLIC = 'Public'

# Will allow user self registration
# AUTH_USER_REGISTRATION = True

# The default user self registration role
# AUTH_USER_REGISTRATION_ROLE = "Public"

# When using OAuth Auth, uncomment to setup provider(s) info
# Google OAuth example:
# OAUTH_PROVIDERS = [{
#   'name':'google',
#     'token_key':'access_token',
#     'icon':'fa-google',
#         'remote_app': {
#             'api_base_url':'https://www.googleapis.com/oauth2/v2/',
#             'client_kwargs':{
#                 'scope': 'email profile'
#             },
#             'access_token_url':'https://accounts.google.com/o/oauth2/token',
#             'authorize_url':'https://accounts.google.com/o/oauth2/auth',
#             'request_token_url': None,
#             'client_id': GOOGLE_KEY,
#             'client_secret': GOOGLE_SECRET_KEY,
#         }
# }]
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