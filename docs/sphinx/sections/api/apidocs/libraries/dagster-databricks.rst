Databricks (dagster-databricks)
-------------------------------

The ``dagster_databricks`` package provides these main pieces of functionality:

- A resource, ``databricks_pyspark_step_launcher``, which will execute a op within a Databricks
  context on a cluster, such that the ``pyspark`` resource uses the cluster's Spark instance.
- An op factory, ``create_databricks_run_now_op``, which creates an op that launches an existing
  Databricks job using the `Run Now API <https://docs.databricks.com/api-explorer/workspace/jobs/runnow>`_.
- A op factory, ``create_databricks_submit_run_op``, which creates an op that submits a one-time run
  of a set of tasks on Databricks using the `Submit Run API <https://docs.databricks.com/api-explorer/workspace/jobs/submit>`_.

Note that, for the ``databricks_pyspark_step_launcher``, either S3 or Azure Data Lake Storage config
**must** be specified for ops to succeed, and the credentials for this storage must also be
stored as a Databricks Secret and stored in the resource config so that the Databricks cluster can
access storage.

.. currentmodule:: dagster_databricks

APIs
----


Resources
=========

.. autoconfigurable:: DatabricksClientResource
  :annotation: ResourceDefinition

.. autoclass:: DatabricksClient
  :members:

Ops
====

.. autofunction:: dagster_databricks.create_databricks_run_now_op

.. autofunction:: dagster_databricks.create_databricks_submit_run_op


Step Launcher
==============
.. autoconfigurable:: dagster_databricks.databricks_pyspark_step_launcher
  :annotation: ResourceDefinition

Pipes
=====

.. autoclass:: PipesDatabricksClient

.. autoclass:: PipesDbfsContextInjector

.. autoclass:: PipesDbfsMessageReader

Other
=====

.. autoclass:: dagster_databricks.DatabricksError


Legacy
======

.. autoconfigurable:: databricks_client
  :annotation: ResourceDefinition
