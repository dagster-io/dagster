Deploying Dagster
-----------------

Quick Start
~~~~~~~~~~~

Dagster supports a wide variety of deployment environments. You can find a full guide to the
different components of a Dagster deployment in the `reference guide <reference.html>`_.

When configuring a Dagster deployment, at minimum you'll likely want to configure up two things:
**execution** and **storage**:

.. rubric:: Execution

Out of the box, Dagster runs single-process execution. To enable multi-process execution, add the
following to your pipeline configuration YAML:

.. code-block:: yaml
    :caption: execution_config.yaml

    execution:
      multiprocess:
        config:
          max_concurrent: 0
    storage:
      filesystem:


Any pipelines that are configured with this YAML will execute in multiprocess mode. Note that
setting ``max_concurrent`` to 0 implies setting concurrency of
:py:func:`python:multiprocessing.cpu_count`. Along with native execution, Dagster supports other
execution engines including `Airflow <other/airflow.html>`_ and `Dask <other/dask.html>`_; check out
the `reference guide <reference.html>`_ for more information.

.. rubric:: Storage
The best place to start is to set the environment variable ``$DAGSTER_HOME`` to a local folder in
the environment where you run Dagster/Dagit. The system will then use that folder for run/events and
logs storage.

In a production context with large-scale data, you'll want to consider storing data elsewhere.

Runs and events use local SQLite databases in ``$DAGSTER_HOME`` by default; we also support
PostgreSQL storage. To use PostgreSQL for runs and events storage, add the following lines to your
``$DAGSTER_HOME/dagster.yaml``:

.. code-block:: yaml
   :caption: dagster.yaml

    run_storage:
        module: dagster_postgres.run_storage
        class: PostgresRunStorage
        config:
            postgres_url: "postgresql://{username}:{password}@{host}:5432/{database}"

    event_log_storage:
        module: dagster_postgres.event_log
        class: PostgresEventLogStorage
        config:
            postgres_url: "postgresql://{username}:{password}@{host}:5432/{database}"

and replace the connection string fields indicated with the appropriate configuration for your
environment.

System storage is set to in-memory by default. For pipelines which execute in multi-process mode or
otherwise need to share data across process or machine boundaries, intermediates should be stored
elsewhere—this is why we set storage to filesystem for the multiprocess execution configuration
above.

In general, intermediates can be stored on the filesystem by configuring storage in your pipeline
configuration YAML:

.. code-block:: yaml
    :caption: execution_config.yaml

    storage:
      filesystem:
        config:
          base_dir: /tmp/foo/


More Information
~~~~~~~~~~~~~~~~

.. toctree::
  :maxdepth: 1

  local
  aws
  gcp
  reference
  other/index
