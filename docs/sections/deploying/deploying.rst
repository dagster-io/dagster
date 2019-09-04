Deploying
=======================

As is the case with all workflow orchestration, when deploying Dagster pipelines there are two
primary concerns: **execution** and **scheduling**.

In the simplest case where you just want to schedule a simple pipeline or two and solid execution is
relatively lightweight, you can readily schedule and invoke Dagster pipeline execution via cron on
your local machine by adding a ``dagster pipeline execute...`` line to your crontab.

In real-world systems, you'll likely need more sophisticated support for both scheduling and
execution of Dagster pipelines. For this, Dagster provides support for several execution substrates:

- Standalone: Dagit can run as a standalone service, running on a single VM or in a Docker
  container. Dagster has out of the box support for multiprocessing execution.
- `Dask <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-dask>`__:
  distributes execution on a Dask cluster, but relies on cron or a similar external scheduler for
  initiating execution.
- `Airflow <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-airflow>`__:
  Compiles Dagster pipelines into Airflow DAGs for execution; delegates both scheduling and
  pipeline execution to Airflow.

In the following sections, we detail how to operationalize Dagster execution on each of these
systems.

.. toctree::
  :maxdepth: 1

  dagit
  airflow
  dask
