Deploying
=========

As is the case with all workflow orchestration, when deploying Dagster pipelines you are faced with
concerns around **execution**, **scheduling**, and **storage**.

* Execution
  Dagster out of the box supports single and multi process executors. These executors work well for pipelines of moderate size
  or if your pipelines leverage external systems or clusters for heavy compute tasks.

  `dagster-dask <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-dask>`__
  makes Dask available as another alternative for distributed execution. See the guide below for more details on using Dask.

* Scheduling
  Dagster offers a scheduler backed by system cron via the package
  `dagster-cron <https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-cron>`__ .
  These schedules are managed in code and deployed using Dagit or the Dagster CLI.

  Scheduling can also be achieved by deploying to
  `Airflow <https://github.com/dagster-io/dagster/tree/master/python_modules/dagster-airflow>`__.
  See the guide below for more details.

* Storage
  “Instance” is the concept we use to represent a particular installation or deployment of Dagster. An instance
  represents the collection of systems that are used to control how Dagster persists the artifacts it generates.
  See the guide below for details on how to configure your Dagster instance.


.. toctree::
  :maxdepth: 1

  instance
  dagit
  airflow
  dask
