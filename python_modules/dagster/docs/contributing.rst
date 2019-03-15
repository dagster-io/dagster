Contributing
============

If you are planning to contribute to dagster, you will need to set up a local
development environment.

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Python. Python 3.6 or above recommended.

    Note: If you use Python 3.7 dagster-airflow will not install and run properly
    as airflow is not Python 3.7 compatible. Until [AIRFLOW-2876](https://github.com/apache/airflow/pull/3723)
    is resolved (expected in 1.10.3), Airflow (and, as a consequence, dagster-airflow)
    is incompatible with Python 3.7.

    The rest of the modules will work properly so you can ignore this error and develop the rest
    of the modules.

2. Create and activate a virtualenv.

.. code-block:: console

    $ python3 -m venv dagsterenv
    $ source dagsterenv/bin/activate

3. Run the script dev_env_setup.sh at repo root. This sets up a full
dagster developer environment with all modules and runs tests that
do not require heavy external dependencies such as docker. This will
take a few minutes.

    $ ./dev_env_setup.sh

4. Run some tests manually to make sure things are working.

    $ pytest python_modules/dagster/dagster_tests

Have fun coding!

Running dagit webapp in development
-------------------------------------
For development, run the dagit GraphQL server on a different port than the
webapp, from any directory that contains a repository.yml file. For example:

.. code-block:: console

    $ cd dagster/python_modules/dagster/dagster/dagster_examples
    $ dagit -p 3333

Run the local development (autoreloading, etc.) version of the webapp.

.. code-block:: console

    $ cd dagster/python_modules/dagit/dagit/webapp
    $ REACT_APP_GRAPHQL_URI="http://localhost:3333/graphql" yarn start

To run JavaScript tests for the dagit frontend, you can run:

.. code-block:: console

    $ cd dagster/python_modules/dagit/dagit/webapp
    $ yarn test

In webapp development it's handy to run ``yarn run jest --watch`` to have an
interactive test runner.

Some webapp tests use snapshots--auto-generated results to which the test
render tree is compared. Those tests are supposed to break when you change
something.

Check that the change is sensible and run ``yarn run jest -u`` to update the
snapshot to the new result. You can also update snapshots interactively
when you are in ``--watch`` mode.

Releasing
-----------
Projects are released using the Python script at ``dagster/bin/publish.py``.

Developing docs
---------------
Running a live html version of the docs can expedite documentation development.

.. code-block:: console

    $ cd python_modules/dagster/docs
    $ make livehtml
