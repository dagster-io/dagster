Contributing
=======================

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create and activate virtualenv

::

    python3 -m venv dagsterenv
    source dagsterenv/bin/activate

2. Install dagster locally and install dev tools

::

    cd dagster/python_modules
    pip install -e ./dagit
    pip install -e ./dagster
    pip install -r ./dagster/dev-requirements.txt

3. Install dagit webapp dependencies

::

    cd python_modules/dagit/dagit/webapp
    yarn

4. Run tests

::

    cd python_modules/dagster
    tox
    cd python_modules/dagit
    tox
    cd python_modules/dagit/dagit/webapp
    yarn test

Running dagit webapp in development
-------------------------------------

Run dagit on different port

::

    dagit -p 3333

Run local development version of webapp

::

    cd python_modules/dagit/dagit/webapp
    REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start

Releasing
-----------

Dagster and dagit both have `./bin/publish.sh` scripts.

Developing docs
---------------

::

    cd python_modules/dagster/docs
    make livehtml
