# Execute this script once you have a clean virtual environment
#
# Python Virtual Environment Landscape is insanely fractured. See:
# https://stackoverflow.com/questions/41573587/what-is-the-difference-between-venv-pyvenv-pyenv-virtualenv-virtualenvwrappe
#
# pyenv is recommended for managing different python versions on your machine
#
# Most dagster developers use venv for virtual environment management
#!/bin/bash -ex

pip install --upgrade pip
pip install -r bin/requirements.txt

pip install -e python_modules/dagster[aws]
pip install -r python_modules/dagster/dev-requirements.txt
python -m pytest python_modules/dagster

pip install python_modules/libraries/dagster-pandas
python -m pytest python_modules/libraries/dagster-pandas

pip install -e python_modules/dagster-graphql
python -m pytest python_modules/dagster-graphql

pip install -e python_modules/dagstermill
python -m pytest python_modules/dagstermill

pip install -e python_modules/dagit
pip install -r python_modules/dagit/dev-requirements.txt
python -m pytest python_modules/dagit

pip install -e python_modules/dagster-graphql
python -m pytest python_modules/dagster-graphql

PYTHON_37 = `python -c 'import sys; exit(1) if sys.version_info.major >= 3 and sys.version_info.minor >= 7 else exit(0)'`

if [! $PYTHON_37]
then
  SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow
  python -m pytest python_modules/dagster-airflow

  airflow initdb

  pip install -e python_modules/airline-demo
  pip install -r python_modules/airline-demo/dev-requirements.txt

  pushd python_modules/airline-demo
  docker-compose up --detach
  popd
  pushd python_modules
  make test_airline
  popd
fi

pip install python_modules/libraries/dagster-aws
python pytest -m python_modules/libraries/dagster-aws

pip install python_modules/libraries/dagster-sqlalchemy
python pytest -m python_modules/libraries/dagster-sqlalchemy

pip install python_modules/libraries/dagster-ge
python pytest -m python_modules/libraries/dagster-ge

pip install python_modules/libraries/dagster-spark
python pytest -m python_modules/libraries/dagster-spark

pip install python_modules/libraries/dagster-snowflake
python pytest -m python_modules/libraries/dagster-snowflake

pip install python_modules/libraries/dagster-pyspark
python pytest -m python_modules/libraries/dagster-pyspark

pushd python_modules
make rebuild_dagit
make black
make pylint
popd

