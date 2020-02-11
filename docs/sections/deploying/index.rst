Deploying Dagster
-----------------

Getting started with Dagster is as easy as running:

.. code-block:: shell

    pip install dagit
    dagit

Dagster supports a wide variety of more sophisticated deployment strategies for production.

Typically, you'll want to deploy Dagit somewhere, configure the way that it stores information and
launches runs, and make sure your pipelines are configured to run appropriately for your
environment.

If you're using the Celery engine, you'll want to run worker processes to parallelize execution.

Alternatively, you may want to deploy Dagster pipelines into a completely different scheduling and
execution environment, like Apache Airflow.

No matter how you're planning to deploy Dagster, you should first understand its default behavior.

You should also be familiar with configuring the Dagster instance, which organizes all of the
information specific to a particular installation or deployment of Dagster, using ``dagster.yaml``.

And you should be aware of the per-pipeline run configuration you'll need for your pipeline runs to
take advantage of the environment in which they're deployed.

.. toctree::
  :maxdepth: 2

  instance
  local
  celery
  aws
  gcp
  dask
  scheduler
  airflow
