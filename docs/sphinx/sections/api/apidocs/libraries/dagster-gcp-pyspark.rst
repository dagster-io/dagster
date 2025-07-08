GCP + PySpark (dagster-gcp-pyspark)
===================================

.. currentmodule:: dagster_gcp_pyspark

Google BigQuery
-----------------
This library provides an integration with the `BigQuery <https://cloud.google.com/bigquery>`_ database and PySpark data processing library.

Related Guides:

* `Using Dagster with BigQuery <https://docs.dagster.io/integrations/libraries/gcp/bigquery>`_
* `BigQuery I/O manager reference <https://docs.dagster.io/integrations/libraries/gcp/bigquery/reference>`_


.. autoconfigurable:: BigQueryPySparkIOManager
  :annotation: IOManagerDefinition

.. autoclass:: BigQueryPySparkTypeHandler

Legacy
------

.. autoconfigurable:: bigquery_pyspark_io_manager
  :annotation: IOManagerDefinition