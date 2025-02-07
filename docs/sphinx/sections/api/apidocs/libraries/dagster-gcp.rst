GCP (dagster-gcp)
=================

.. currentmodule:: dagster_gcp

BigQuery
--------

Related Guides:

* `Using Dagster with BigQuery <https://docs.dagster.io/integrations/libraries/gcp/bigquery/>`_
* `BigQuery I/O manager reference <https://docs.dagster.io/integrations/libraries/gcp/bigquery/reference>`_


BigQuery Resource
^^^^^^^^^^^^^^^^^^

.. autoconfigurable:: BigQueryResource
  :annotation: ResourceDefinition


BigQuery I/O Manager
^^^^^^^^^^^^^^^^^^^^^

.. autoconfigurable:: BigQueryIOManager
  :annotation: IOManagerDefinition


BigQuery Ops
^^^^^^^^^^^^^^^

.. autofunction:: bq_create_dataset

.. autofunction:: bq_delete_dataset

.. autofunction:: bq_op_for_queries

.. autofunction:: import_df_to_bq

.. autofunction:: import_file_to_bq

.. autofunction:: import_gcs_paths_to_bq


Data Freshness
^^^^^^^^^^^^^^

.. autofunction:: fetch_last_updated_timestamps

Other
^^^^^^^

.. autoclass:: BigQueryError

GCS
---

GCS Resource
^^^^^^^^^^^^^

.. autoconfigurable:: GCSResource
  :annotation: ResourceDefinition


GCS I/O Manager
^^^^^^^^^^^^^^^^^^

.. autoconfigurable:: GCSPickleIOManager
  :annotation: IOManagerDefinition


GCS Sensor
^^^^^^^^^^

.. autofunction:: dagster_gcp.gcs.sensor.get_gcs_keys


File Manager
^^^^^^^^^^^^

.. autoclass:: GCSFileHandle
  :members:

.. autoconfigurable:: GCSFileManagerResource
  :annotation: ResourceDefinition

GCS Compute Log Manager
^^^^^^^^^^^^^^^^^^^^^^^^
.. autoclass:: dagster_gcp.gcs.GCSComputeLogManager

Dataproc
--------

Dataproc Resource
^^^^^^^^^^^^^^^^^^

.. autoconfigurable:: DataprocResource
  :annotation: ResourceDefinition

Dataproc Ops
^^^^^^^^^^^^^^

.. autoconfigurable:: dataproc_op

.. currentmodule:: dagster_gcp.pipes

Pipes
--------------

Clients
^^^^^^^

.. autoclass:: dagster_gcp.pipes.PipesDataprocJobClient

Context Injectors
^^^^^^^^^^^^^^^^^

.. autoclass:: dagster_gcp.pipes.PipesGCSContextInjector

Message Readers
^^^^^^^^^^^^^^^

.. autoclass:: dagster_gcp.pipes.PipesGCSMessageReader

.. currentmodule:: dagster_gcp

Legacy
------

.. autoconfigurable:: ConfigurablePickledObjectGCSIOManager
  :annotation: IOManagerDefinition

.. autoconfigurable:: bigquery_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: build_bigquery_io_manager
  :annotation: IOManagerDefinition

.. autoconfigurable:: gcs_resource
  :annotation: ResourceDefinition

.. autoconfigurable:: gcs_pickle_io_manager
  :annotation: IOManagerDefinition

.. autodata:: gcs_file_manager
  :annotation: ResourceDefinition

.. autoconfigurable:: dataproc_resource
  :annotation: ResourceDefinition
