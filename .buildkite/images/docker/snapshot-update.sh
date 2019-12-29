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
pyenv virtualenv 3.7.5 snapshot-reqs-3
pyenv activate snapshot-reqs-3
pip install -U pip setuptools wheel
make install_dev_python_modules


# See issue: https://github.com/dagster-io/dagster/issues/1295
#
# These sed updates take the dependency created by the above `make install_dev_python_modules` and
# add PEP 496 environment markers, primarily because many libraries have deprecated support for
# Python 3.5. For example, the dep:
#
# marshmallow-sqlalchemy==0.21.0
#
# becomes:
#
# marshmallow-sqlalchemy==0.21.0; python_version>'3.5'
# marshmallow-sqlalchemy==0.19.0; python_version<='3.5'
#
# Since we include the matched \1 on the RHS of the sed command, we preserve the original version
# for python_version>'3.5'.
#
# Summary of updates:
#   * sphinx-contrib images: https://github.com/dagster-io/dagster/issues/1858
#   * Black is not supported on py35
#   * Tensorflow is not (yet) supported on py38
#   * matplotlib not supported on py38 yet
#   * Need different versions for py35:
#       Flask-AppBuilder, dask/distributed, ipython, marshmallow-sqlalchemy, prompt-toolkit
pip freeze --exclude-editable \
    | sed -E 's|sphinxcontrib-images.*|git+https://github.com/t-b/sphinxcontrib-images.git@c76b9c25efb249f9c5054adbb436455095c6d2f7#egg=sphinxcontrib-images|' \
    | sed -E "s|(Flask-AppBuilder.*)|\1; python_version>'3.5'^Flask-AppBuilder==1.13.1; python_version<='3.5'|" | tr '^' '\n' \
    | sed -E "s|(dask.*)|\1; python_version>'3.5'^dask==2.6.0; python_version<='3.5'|" | tr '^' '\n' \
    | sed -E "s|(distributed.*)|\1; python_version>'3.5'^distributed==2.6.0; python_version<='3.5'|" | tr '^' '\n' \
    | sed -E "s|(ipython==.*)|\1; python_version>'3.5'^ipython==7.9.0; python_version<='3.5'|" | tr '^' '\n' \
    | sed -E "s|(black.*)|\1; python_version >= '3.6'|" \
    | sed -E "s|(tensorflow.*==.*)|\1; python_version <= '3.7'|" \
    | sed -E "s|(matplotlib.*)|\1; python_version <= '3.7'|" | tr '^' '\n' \
    | sed -E "s|(marshmallow-sqlalchemy.*)|\1; python_version>'3.5'^marshmallow-sqlalchemy==0.19.0; python_version<='3.5'|" | tr '^' '\n' \
    | sed -E "s|(prompt-toolkit.*)|\1; python_version>'3.5'^prompt-toolkit==2.0.10; python_version<='3.5'|" | tr '^' '\n' \
    > $ROOT/.buildkite/images/docker/snapshot-reqs-3.txt

# Freeze python 2 deps
pyenv virtualenv 2.7.17 snapshot-reqs-2
pyenv activate snapshot-reqs-2
pip install -U pip setuptools wheel
make install_dev_python_modules

# Notes on sed updates:
#   * https://github.com/dagster-io/dagster/issues/1858
pip freeze --exclude-editable \
    | sed -E 's|sphinxcontrib-images.*|git+https://github.com/t-b/sphinxcontrib-images.git@c76b9c25efb249f9c5054adbb436455095c6d2f7#egg=sphinxcontrib-images|' \
    > $ROOT/.buildkite/images/docker/snapshot-reqs-2.txt
