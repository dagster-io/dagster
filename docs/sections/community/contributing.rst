Contributing
============
If you are planning to contribute to Dagster, you will first need to set up a local development
environment.

Environment Setup
~~~~~~~~~~~~~~~~~

1. Install Python. Python 3.6 or above recommended, but our CI/CD pipeline currently tests against
the Python versions 2.7, 3.5, 3.6, and 3.7.

2. Create and activate a virtualenv, preferably through ``pyenv``. On macOS:

.. code-block:: console

    $ brew install pyenv pyenv-virtualenv
    $ pyenv install 3.7.4
    $ pyenv virtualenv 3.7.4 dagster37
    $ pyenv activate dagster37

3. Install yarn. If you are on macOS, this should be:

.. code-block:: console

    $ brew install yarn

4. Run the ``make dev_install`` at repo root. This sets up a full dagster developer environment with
   all modules and runs tests that do not require heavy external
   dependencies such as docker. This will take a few minutes.

.. code-block:: console

    $ make dev_install

5. Run some tests manually to make sure things are working:

.. code-block:: console

    $ python -m pytest python_modules/dagster/dagster_tests

Have fun coding!

Developing Dagster
~~~~~~~~~~~~~~~~~~~~~

Some notes on developing in Dagster:

- **Python 2**: We plan to continue supporting Python 2 for some time; it is worth testing your changes with
  Python 2 to ensure compatibility.

- **Black/Pylint**: We use `black <https://github.com/python/black>`_ to enforce a consistent code
  style, along with `pylint <https://www.pylint.org/>`_. We test these in our CI/CD pipeline.

- **Line Width**: We use a line width of 100.

- **IDE**: We recommend setting up your IDE to format with black on save and check pylint,
  but you can always run ``make black`` and ``make pylint`` in the root Dagster directory before
  submitting a pull request. If you're also using VS Code, you can see what we're using for our
  ``settings.json`` `here <https://gist.github.com/natekupp/7a17a9df8d2064e5389cc84aa118a896>`_.


Developing Dagit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
For development, run the dagit GraphQL server on a different port than the webapp, from any
directory that contains a repository.yaml file. For example:

.. code-block:: console

    $ cd dagster/examples/dagster_examples/intro_tutorial
    $ dagit -p 3333

Keep this running. Then, in another terminal, run the local development
(autoreloading, etc.) version of the webapp:

.. code-block:: console

    $ cd dagster/js_modules/dagit
    $ make dev_webapp

To run JavaScript tests for the dagit frontend, you can run:

.. code-block:: console

    $ cd dagster/js_modules/dagit
    $ yarn test

In webapp development it's handy to run ``yarn run jest --watch`` to have an interactive test
runner.

Some webapp tests use snapshots--auto-generated results to which the test render tree is compared.
Those tests are supposed to break when you change something.

Check that the change is sensible and run ``yarn run jest -u`` to update the snapshot to the new
result. You can also update snapshots interactively when you are in ``--watch`` mode.

Developing Docs
~~~~~~~~~~~~~~~
Running a live html version of the docs can expedite documentation development:

.. code-block:: console

    $ cd docs
    $ make livehtml

Our documentation employs a combination of Markdown and reStructuredText.