Quick start
-----------

.. toctree::
  :hidden:
  :maxdepth: 2

  self
  packages
  python
  telemetry


To install dagster and dagit into an existing Python environment, run:

.. code-block:: console

    $ pip install dagster dagit

This will install the latest stable version of the core dagster packages in your
current Python environment.

Dagster is tested on Python 3.7.4, 3.6.9, 3.5.7, and 2.7.16.

Using Python 3 is strongly encouraged. As a reminder, the
`official EOL <https://www.python.org/doc/sunset-python-2/>`_ for Python 2 was
January 1, 2020.

To check that Python and the pip package manager are already installed in your
environment, you can run:

.. code-block:: console

    $ python --version
    $ pip --version

We strongly recommend installing dagster inside a Python virtualenv. If you are
running Anaconda, you should install dagster inside a Conda environment.

If you would like to install dagster from source, please see the section on
:ref:`Contributing <Contributing>`.
