Installation
=======================

Dagster is tested on Python 3.6.6, 3.5.6, and 2.7.15. Python 3 is strongly
encouraged -- if you can, you won't regret making the switch!
  * You can't use Python 3.7+ yet because of
    https://github.com/apache/arrow/issues/1125

Installing Python, pip, and virtualenv
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To check that Python, the pip package manager, and virtualenv (highly
recommended) are already installed, you can run:
::
    python --version
    pip --version
    virtualenv --version

If these tools aren't present on your system, you can install them as follows:

On Ubuntu:
::
    sudo apt update
    sudo apt install python3-dev python3-pip
    sudo pip3 install -U virtualenv  # system-wide install

On OSX, using `Homebrew <https://brew.sh/>`_:
::
    brew update
    brew install python  # Python 3
    sudo pip3 install -U virtualenv  # system-wide install

On Windows (Python 3):
- Install the *Microsoft Visual C++ 2015 Redistributable Update 3*. This
  comes with *Visual Studio 2015* but can be installed separately as follows:
    1. Go to the Visual Studio downloads,
    2. Select *Redistributables and Build Tools*,
    3. Download and install the *Microsoft Visual C++ 2015 Redistributable
       Update 3*.
- Install the 64-bit Python 3 release for Windows (select ``pip`` as an
  optional feature).
- Then run ``pip3 install -U pip virtualenv``


Installing the stable version from PyPI
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
We strongly recommend installing dagster inside a Python virtualenv. On
Python 3, you can just run:
::
    python3 -m venv /path/to/new/virtual/environment

This will create a new Python environment whose interpreter and libraries
are isolated from those installed in other virtual environments, and
(by default) any libraries installed in a “system” Python installed as part
of your operating system



To install dagster and dagit, run:

::
    pip install dagster
    pip install dagit


Installing the latest version from Github
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. Installing the stable version using Anaconda
.. ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
render tree is compared. Those tests are supposed to break when you change
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
