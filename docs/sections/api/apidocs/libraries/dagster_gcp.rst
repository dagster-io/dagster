GCP (dagster_gcp)
=================

.. currentmodule:: dagster_gcp

BigQuery
--------

.. autoclass:: BigQueryError

.. autodata:: bigquery_resource
  :annotation: ResourceDefinition

.. autofunction:: bq_create_dataset

.. autofunction:: bq_delete_dataset

.. autofunction:: bq_solid_for_queries

.. autofunction:: import_df_to_bq

.. autofunction:: import_file_to_bq

.. autofunction:: import_gcs_paths_to_bq


Dataproc
--------

.. autofunction:: dataproc_solid

.. autodata:: dataproc_resource
  :annotation: ResourceDefinition


GCS
---

.. autodata:: gcs_system_storage
  :annotation: SystemStorageDefinition


.. autodata:: dagster_gcp.gcs.gcs_intermediate_storage
  :annotation: IntermediateStorageDefinition

.. autodata:: gcs_resource
  :annotation: ResourceDefinition
