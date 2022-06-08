GCP (dagster-gcp)
=================

.. currentmodule:: dagster_gcp

BigQuery
--------

.. autoclass:: BigQueryError

.. autoconfigurable:: bigquery_resource
  :annotation: ResourceDefinition

.. autofunction:: bq_create_dataset

.. autofunction:: bq_delete_dataset

.. autofunction:: bq_op_for_queries

.. autofunction:: import_df_to_bq

.. autofunction:: import_file_to_bq

.. autofunction:: import_gcs_paths_to_bq


Dataproc
--------

.. autoconfigurable:: dataproc_op

.. autoconfigurable:: dataproc_resource
  :annotation: ResourceDefinition


GCS
---

.. autoconfigurable:: gcs_resource
  :annotation: ResourceDefinition

.. autoclass:: GCSFileHandle
  :members:

.. autodata:: gcs_file_manager
  :annotation: ResourceDefinition

.. autoconfigurable:: dagster_gcp.gcs.gcs_pickle_io_manager
  :annotation: IOManagerDefinition

Legacy APIs
-----------

.. autofunction:: bq_solid_for_queries

.. autofunction:: dataproc_solid