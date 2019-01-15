Contributing
============

If you are planning to contribute to dagster, you will need to set up a local
development environment.

Local development setup
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Install Python 3.6.
  * You can't use Python 3.7+ yet because of https://github.com/apache/arrow/issues/1125

2. Create and activate a virtualenv

.. code-block:: console

    $ python3 -m venv dagsterenv
    $ source dagsterenv/bin/activate

3. Install dagster locally and install dev tools

.. code-block:: console

    $ git clone git@github.com:dagster-io/dagster.git
    $ cd dagster/python_modules
    $ pip install -e ./dagit
    $ pip install -e ./dagster
    $ pip install -r ./dagster/dev-requirements.txt

4. Install dagit webapp dependencies

.. code-block:: console

    $ cd dagster/python_modules/dagit/dagit/webapp
    $ yarn install

5. Run tests

We use tox to manage test environments for python.

.. code-block:: console

    $ cd dagster/python_modules/dagster
    $ tox
    $ cd dagster/python_modules/dagit
    $ tox

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

Releasing
-----------
Projects are released using the Python script at ``dagster/bin/publish.py``.

Developing docs
---------------
Running a live html version of the docs can expedite documentation development.

.. code-block:: console

    $ cd python_modules/dagster/docs
    $ make livehtml
