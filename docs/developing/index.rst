Local development setup
=======================

1. Create and activate virtualenv

::

    python3 -m venv dagsterenv
    source dagsterenv/bin/activate

2. Install dagster locally and install dev tools

::

    pip install -e ./dagster
    pip install -r ./dagster/dev-requirements.txt

3. Install pre-commit hooks

::

    pre-commit install

4. Run tests

::

    tox

Developing docs
---------------

::

    cd docs
    make livehtml
