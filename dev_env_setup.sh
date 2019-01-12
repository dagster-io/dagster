# Execute this script once you have a clean virtual environment
#
# Python Virtual Environment Landscape is insanely fractured. See:
# https://stackoverflow.com/questions/41573587/what-is-the-difference-between-venv-pyvenv-pyenv-virtualenv-virtualenvwrappe
#
# pyenv is recommended for managing different python versions on your machine
#
# Most dagster developers use venv for virtual environment management

pip install --upgrade pip
pip install -e python_modules/dagster
pip install -r python_modules/dagster/requirements.txt
pip install -r python_modules/dagster/dev-requirements.txt

python -m pytest python_modules/dagster

pip install -e python_modules/dagstermill

python -m pytest python_modules/dagstermill

pip install -e python_modules/dagster-pandas
python -m pytest python_modules/dagster-pandas

pip install -e python_modules/dagster-sqlalchemy
python -m pytest python_modules/dagster-sqlalchemy

pip install -e python_modules/dagit
pip install -r python_modules/dagit/dev-requirements.txt

python -m pytest python_modules/dagit

pip install -e python_modules/dagster-ge
python -m pytest python_modules/dagster-ge

pip install -e python_modules/airline-demo
pip install -r python_modules/airline-demo/dev-requirements.txt

pushd python_modules/airline-demo
docker-compose up --detach
popd
pushd python_modules
make test_airline
popd
