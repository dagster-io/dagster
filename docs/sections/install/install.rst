Install
-------

Quick start
===========

To install dagster and dagit into an existing Python environment, run:

.. code-block:: console

    $ pip install dagster dagit

This will install the latest stable version of the core dagster packages in your current Python
environment.

If you would like to install dagster from source, please see the section on :ref:`Contributing <Contributing>`.

Dagster packages
==================

Dagster is a highly componentized system consisting of a number of core packages.

    - **dagster** contains the core programming model and the ``dagster`` CLI tool for executing
      and managing pipelines.
    - **dagster-graphql** defines a `GraphQL <https://graphql.org/>`_ API for executing and managing
      pipelines and their outputs and includes a CLI tool for executing queries against the API.
    - **dagit** is our powerful GUI tool for exploring, managing, scheduling, and monitoring
      dagster pipelines, written against the GraphQL API.
    - **dagster-airflow** provides a facility for compiling dagster pipelines to Airflow DAGs so
      that they can be scheduled and orchestrated using `Apache Airflow <https://airflow.apache.org/>`_.
    - **dagster-dask** provides a pluggable execution engine for dagster pipelines so they can be
      executed using the `Dask <https://dask.org/>`_ framework for parallel computing.
    - **dagstermill** provides the ability to wrap `Jupyter <https://jupyter.org/>`_ notebooks as
      dagster solids for repeatable execution as part of dagster pipelines.

Dagster also provides a large set of optional add-on libraries that integrate with other parts of
the data ecosystem.

    - **dagster-aws** includes facilities for working with
      `Amazon Web Services <https://aws.amazon.com/>`_, including Cloudwatch for logging, EMR for
      hosted cluster compute, S3 for persistent storage of logs and intermediate artifacts, and
      a CLI tool to streamline deployment of hosted dagit to AWS.
    - **dagster-bash** includes library solids to execute bash commands.
    - **dagster-cron** includes a simple scheduler that integrates with dagit, built on cron.
    - **dagster-datadog** includes a resource wrapping the dogstatsd library for reporting
      metrics to `Datadog <https://www.datadoghq.com/product/>`_.
    - **dagster-dbt** includes library solids to wrap invocations of
      `dbt <https://www.getdbt.com/>`_.
    - **dagster-gcp** includes facilities for working with
      `Google Cloud Platform <https://cloud.google.com/>`_, including BigQuery databases and
      Dataproc for hosted cluster compute.
    - **dagster-ge** includes tools for working with the
      `Great Expectations <https://greatexpectations.io/>`_ data quality testing library.
    - **dagster-pagerduty** includes a resource that lets you trigger
      `PagerDuty <https://www.pagerduty.com/>`_ alerts from within dagster pipelines.
    - **dagster-pandas** includes tools for working with the common
      `Pandas <https://pandas.pydata.org/>`_ library for Python data frames.
    - **dagster-papertrail** includes facilities for logging to
      `Papertrail <https://papertrailapp.com/>`_.
    - **dagster-postgres** includes pluggable Postgres-backed storage for run history and event
      logs, allowing dagit and other dagster tools to point at shared remote databases. 
    - **dagster-pyspark** includes datatypes for working with
      `PySpark <https://spark.apache.org/docs/latest/api/python/index.html>`_ data frames in
      dagster pipelines.
    - **dagster-slack** includes a resource that lets you post to `Slack <https://slack.com/>`_
      from within dagster pipelines.
    - **dagster-snowflake** includes resources and solids for connecting to and querying
      `Snowflake <https://www.snowflake.com/>`_ data warehouses.
    - **dagster-spark** includes solids for working with `Spark <https://spark.apache.org/>`_ jobs.
    - **dagster-ssh** includes resources and solids for SSH and SFTP execution.
    - **dagster-twilio** includes a resource that makes a `Twilio <https://www.twilio.com/>`_
      client available within dagster pipelines.


Installing Python and pip
=========================

Dagster is tested on Python 3.7.4, 3.6.9, 3.5.7, and 2.7.16.

Using Python 3 is strongly encouraged. As a
reminder, the `official EOL <https://www.python.org/doc/sunset-python-2/>`_ for Python 2 is
January 1, 2020.

To check that Python and the pip package manager are already installed in your environment, you
can run:

.. code-block:: console

    $ python --version
    $ pip --version

If you're running Python 3.3 or later, you already have the venv package for managing
virtualenvs. On Python 2.7, you can check whether you have the virtualenv tool installed by
running:

.. code-block:: console

    $ virtualenv --version

If these tools aren't present on your system, you can install them as follows:

.. rubric:: Installing Python on Ubuntu

.. code-block:: console

    $ sudo apt update
    $ sudo apt install python3-dev python3-pip

This will install Python 3 and pip on your system.

.. rubric:: Installing Python on macOS

Using `Homebrew <https://brew.sh/>`_:

.. code-block:: console

    $ brew update
    $ brew install python  # Python 3

This will install Python 3 on your system.

If you are using the macOS-provided Python 2.7, you can install virtualenv with:

.. code-block:: console

    $ sudo pip install -U virtualenv  # system-wide install

.. rubric:: Installing Python on Windows

- Install the *Microsoft Visual C++ 2015 Redistributable Update 3*. This comes with *Visual Studio 2015* but can be installed separately as follows:

  1. Go to the Visual Studio downloads,
  2. Select *Redistributables and Build Tools*,
  3. Download and install the *Microsoft Visual C++ 2015 Redistributable Update 3*.

- Install the 64-bit Python 3 release for Windows (select ``pip`` as an optional feature).

To use the ``dagit`` tool, you will also need to
`install yarn <https://yarnpkg.com/lang/en/docs/install/>`_.


.. rubric:: Notes on Python virtualenvs

We strongly recommend installing dagster inside a Python virtualenv.

If you are running Anaconda, you should install dagster inside a Conda environment.

To create a virtual environment on Python 3, you can just run:

.. code-block:: console

    $ python3 -m venv ~/.venvs/dagster

This will create a new Python environment whose interpreter and libraries
are isolated from those installed in other virtual environments, and
(by default) any libraries installed in a “system” Python installed as part
of your operating system.

On Python 2, you can use a tool like
`virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/>`_
to manage your virtual environments, or just run:

.. code-block:: console

    $ virtualenv ~/.venvs/dagster

You'll then need to 'activate' the virtualenvironment, in bash by
running:

.. code-block:: console

    $ source ~/.venvs/dagster/bin/activate

(For other shells, see the
`venv documentation <https://docs.python.org/3/library/venv.html#creating-virtual-environments>`_.)

If you are using Anaconda, you can run:

.. code-block:: console

    $ conda create --name dagster

And then, on macOS or Ubuntu:

.. code-block:: console

    $ source activate dagster

Or, on Windows:

.. code-block:: console

    $ activate dagster
