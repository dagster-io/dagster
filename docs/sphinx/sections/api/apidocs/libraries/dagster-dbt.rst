#################
dbt (dagster-dbt)
#################

Dagster orchestrates dbt alongside other technologies, so you can combine dbt with Spark, Python,
etc. in a single workflow. Dagster's software-defined asset abstractions make it simple to define
data assets that depend on specific dbt models, or to define the computation required to compute
the sources that your dbt models depend on.

Related guides: `Visualize and orchestrate assets in dbt Core </integrations/dbt>`_ and
`dbt Cloud <integrations/dbt-cloud>`_.

.. currentmodule:: dagster_dbt

********
dbt Core
********

Here, we provide interfaces to manage dbt projects invoked by the local dbt command line interface
(dbt CLI).

Assets (dbt Core)
=================

.. autofunction:: load_assets_from_dbt_project

.. autofunction:: load_assets_from_dbt_manifest

.. autoclass:: DbtManifestAssetSelection

Resources (dbt Core)
====================

CLI Resources
-------------

.. autoclass:: DbtCliResource

.. autoclass:: DbtCliOutput

.. autoconfigurable:: dbt_cli_resource
    :annotation: ResourceDefinition

*********
dbt Cloud
*********

Here, we provide interfaces to manage dbt projects invoked by the hosted dbt Cloud service.

Assets (dbt Cloud)
==================

.. autofunction:: load_assets_from_dbt_cloud_job

Ops (dbt Cloud)
===============

.. autoconfigurable:: dbt_cloud_run_op

Resources (dbt Cloud)
=====================

.. autoclass:: DbtCloudResourceV2

.. autoconfigurable:: dbt_cloud_resource
    :annotation: ResourceDefinition

*****
Types
*****

.. autoclass:: DbtOutput

.. autoclass:: DbtResource

******
Errors
******

.. autoexception:: DagsterDbtError

.. autoexception:: DagsterDbtCliRuntimeError

.. autoexception:: DagsterDbtCliFatalRuntimeError

.. autoexception:: DagsterDbtCliHandledRuntimeError

.. autoexception:: DagsterDbtCliOutputsNotFoundError

.. autoexception:: DagsterDbtCliUnexpectedOutputError

*****
Utils
*****

.. currentmodule:: dagster_dbt.utils

.. autofunction:: generate_materializations
