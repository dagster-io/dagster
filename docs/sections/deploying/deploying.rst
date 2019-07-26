Deploying
=======================

As is the case with all workflow orchestration, when deploying Dagster pipelines, there are two
primary concerns: **execution** and **scheduling**.

In the simplest case where you just want to schedule a simple pipeline or two and solid execution is
relatively lightweight, you can readily schedule and invoke Dagster pipeline execution via cron by
adding a ``dagster pipeline execute...`` line to your crontab.

In real-world systems, you'll likely need more sophisticated support for both scheduling and
executing pipelines.

For this, Dagster provides support for two execution substrates: `Dask <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-dask>`__,
which distributes execution but still relies on cron or some other external scheduler, and
`Airflow <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-airflow>`__,
to which we delegate both scheduling and execution.

In the following sections, we detail how to operationalize Dagster execution on both of these
systems.

.. toctree::
  :maxdepth: 1

  airflow
  dask
