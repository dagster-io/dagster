GCP + Pandas (dagster-gcp-pandas)
=================================

.. currentmodule:: dagster_gcp_pandas

Google BigQuery
----------------
This library provides an integration with the `BigQuery <https://cloud.google.com/bigquery>`_ database and Pandas data processing library.

Related Guides:

* `Using Dagster with BigQuery <https://docs.dagster.io/integrations/bigquery>`_
* `BigQuery I/O manager reference <https://docs.dagster.io/integrations/bigquery/reference>`_

.. autoconfigurable:: BigQueryPandasIOManager
  :annotation: IOManagerDefinition

.. autoclass:: BigQueryPandasTypeHandler


Legacy
=======

.. autoconfigurable:: bigquery_pandas_io_manager
  :annotation: IOManagerDefinition