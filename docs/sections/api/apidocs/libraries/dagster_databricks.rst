Databricks (dagster_databricks)
-------------------------------

The ``dagster_databricks`` package provides two main pieces of functionality:

- a resource, ``databricks_pyspark_step_launcher``, which will execute a solid within a Databricks
  context on a cluster, such that the ``pyspark`` resource uses the cluster's Spark instance; and
- a solid, ``DatabricksRunJobSolidDefinition``, which submits an external configurable job to
  Databricks using the 'Run Now' API.

See the 'simple_pyspark' Dagster example for an example of how to use the resource.

Note that either S3 or Azure Data Lake Storage config **must** be specified for solids to succeed,
and the credentials for this storage must also be stored as a Databricks Secret and stored in the
resource config so that the Databricks cluster can access storage.

.. currentmodule:: dagster_databricks

.. autodata:: dagster_databricks.databricks_pyspark_step_launcher
  :annotation: ResourceDefinition

.. autoclass:: dagster_databricks.DatabricksRunJobSolidDefinition

.. autoclass:: dagster_databricks.DatabricksJobRunner

.. autoclass:: dagster_databricks.DatabricksError
