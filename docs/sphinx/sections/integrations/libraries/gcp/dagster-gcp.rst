###################
dagster-gcp library
###################

.. currentmodule:: dagster_gcp

********
BigQuery
********

Related guides:

* `Using Dagster with BigQuery <https://docs.dagster.io/integrations/libraries/gcp/bigquery>`_
* `BigQuery I/O manager reference <https://docs.dagster.io/integrations/libraries/gcp/bigquery/reference>`_


BigQuery resource
=================

.. autoconfigurable:: BigQueryResource
  :annotation: ResourceDefinition


BigQuery I/O manager
====================

.. autoconfigurable:: BigQueryIOManager
  :annotation: IOManagerDefinition


BigQuery ops
============

.. autofunction:: bq_create_dataset

.. autofunction:: bq_delete_dataset

.. autofunction:: bq_op_for_queries

.. autofunction:: import_df_to_bq

.. autofunction:: import_file_to_bq

.. autofunction:: import_gcs_paths_to_bq


Data freshness
==============

.. autofunction:: fetch_last_updated_timestamps

Other
=====

.. autoclass:: BigQueryError

***
GCS
***

GCS resource
============

.. autoconfigurable:: GCSResource
  :annotation: ResourceDefinition


GCS I/O manager
===============

.. autoconfigurable:: GCSPickleIOManager
  :annotation: IOManagerDefinition


GCS sensor
==========

.. autofunction:: dagster_gcp.gcs.sensor.get_gcs_keys


File manager
============

.. autoclass:: GCSFileHandle
  :members:

.. autoconfigurable:: GCSFileManagerResource
  :annotation: ResourceDefinition

GCS compute log manager
=======================

.. autoclass:: dagster_gcp.gcs.GCSComputeLogManager

********
Dataproc
********

Dataproc resource
=================

.. autoconfigurable:: DataprocResource
  :annotation: ResourceDefinition

Dataproc ops
============

.. autoconfigurable:: dataproc_op

.. currentmodule:: dagster_gcp.pipes

*****
Pipes
*****

Clients
=======

.. autoclass:: dagster_gcp.pipes.PipesDataprocJobClient

Context injectors
=================

.. autoclass:: dagster_gcp.pipes.PipesGCSContextInjector

Message readers
===============

.. autoclass:: dagster_gcp.pipes.PipesGCSMessageReader

.. currentmodule:: dagster_gcp

******
Legacy
******

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

**********
Components
**********

Resource components for use with Dagster's component system.

Resource components
===================

.. autoclass:: dagster_gcp.BigQueryResourceComponent

.. autoclass:: dagster_gcp.GCSResourceComponent

.. autoclass:: dagster_gcp.GCSFileManagerResourceComponent

.. autoclass:: dagster_gcp.DataprocResourceComponent
