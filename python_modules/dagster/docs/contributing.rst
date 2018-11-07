Contributing
=======================

To contribute to dagster you will need to set up a local development environment.

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Python 3.6.
  * You can't use Python 3.7+ yet because of https://github.com/apache/arrow/issues/1125

2. Create and activate a virtualenv

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

    cd dagster/python_modules/dagit/dagit/webapp
    yarn install

4. Run tests

::

    cd dagster/python_modules/dagster
    tox
    cd dagster/python_modules/dagit
    tox
    cd dagster/python_modules/dagit/dagit/webapp
    yarn test

In webapp development it's handy to run `yarn run jest --watch` to have an
interactive test runner.

Some webapp tests use snapshots - auto-generated results to which the test
rener tree is compared. Those tests are supposed to break when you change
something, check that the change is sensible and run `yarn run jest -u` to
update snapshot to the new result. You can also update snapshots interactively
when you are in `--watch` mode.

Running dagit webapp in development
-------------------------------------

For development, run the dagit GraphQL server on a different port than the
webapp, from any directory that contains a repository.yml file. For example:

::

    cd dagster/python_modules/dagster/dagster/dagster_examples
    dagit -p 3333

Run the local development (autoreloading, etc.) version of the webapp.

::

    cd dagster/python_modules/dagit/dagit/webapp
    REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start

Releasing
-----------

Dagster and dagit both have `./bin/publish.sh` scripts.

Developing docs
---------------

Running a live html version of the docs can expedite documentation development.

::

    cd python_modules/dagster/docs
    make livehtml
