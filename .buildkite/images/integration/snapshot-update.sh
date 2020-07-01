#! /bin/bash

set -e

ROOT=$(git rev-parse --show-toplevel)

function cleanup {
    pyenv virtualenv-delete -f snapshot-reqs-3
    pyenv virtualenv-delete -f snapshot-reqs-2
}

# ensure cleanup happens on error or normal exit
trap cleanup EXIT

# Makefile for install_dev_python_modules is at $ROOT/Makefile
pushd $ROOT

# Clean up
find . -name '*.egg-info' | xargs rm -rf
find . -name '__pycache__' | xargs rm -rf
find . -name '*.pyc' | xargs rm -rf

eval "$(pyenv init -)"

# Freeze python 3 deps
pyenv virtualenv 3.7.7 snapshot-reqs-3
pyenv activate snapshot-reqs-3
pip install -U pip setuptools wheel
make install_dev_python_modules

# Freeze python 2 deps
pyenv virtualenv 2.7.17 snapshot-reqs-2
pyenv activate snapshot-reqs-2
pip install -U pip setuptools wheel
make install_dev_python_modules

pip freeze --exclude-editable \
    > $ROOT/.buildkite/images/docker/snapshot-reqs-2.txt
