#! /bin/bash
ROOT=$(git rev-parse --show-toplevel)
pushd $ROOT/.buildkite/images/docker/

function cleanup {
    pyenv virtualenv-delete -f snapshot-reqs-2
    pyenv virtualenv-delete -f snapshot-reqs-3
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

# Freeze python 3 deps. Use 3.5.6 because 3.6+ will install black which is incompatible with < 3.6
pyenv virtualenv 3.5.6 snapshot-reqs-3
pyenv activate snapshot-reqs-3
pip install -U pip setuptools wheel
make install_dev_python_modules
pip freeze --exclude-editable > $ROOT/.buildkite/images/docker/snapshot-reqs-3.txt

# Freeze python 2 deps
pyenv virtualenv 2.7.15 snapshot-reqs-2
pyenv activate snapshot-reqs-2
pip install -U pip setuptools wheel
make install_dev_python_modules
pip freeze --exclude-editable > $ROOT/.buildkite/images/docker/snapshot-reqs-2.txt
