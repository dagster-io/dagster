Databricks (dagster_databricks)
-------------------------------

The ``dagster_databricks`` package provides two main pieces of functionality:

- A resource, ``databricks_pyspark_step_launcher``, which will execute a solid within a Databricks
  context on a cluster, such that the ``pyspark`` resource uses the cluster's Spark instance.
- A function, ``create_databricks_job_solid``, which creates a solid that submits an external
  configurable job to Databricks using the 'Run Now' API.

Note that, for the ``databricks_pyspark_step_launcher``, either S3 or Azure Data Lake Storage config
**must** be specified for solids to succeed, and the credentials for this storage must also be
stored as a Databricks Secret and stored in the resource config so that the Databricks cluster can
access storage.

.. currentmodule:: dagster_databricks

.. autofunction:: dagster_databricks.create_databricks_job_solid

.. autodata:: dagster_databricks.databricks_pyspark_step_launcher
  :annotation: ResourceDefinition

.. autoclass:: dagster_databricks.DatabricksError
