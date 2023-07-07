#################
dbt (dagster-dbt)
#################

Dagster orchestrates dbt alongside other technologies, so you can combine dbt with Spark, Python,
etc. in a single workflow. Dagster's software-defined asset abstractions make it simple to define
data assets that depend on specific dbt models, or to define the computation required to compute
the sources that your dbt models depend on.

Related documentation pages: `dbt </integrations/dbt>`_ and
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

Ops (dbt Core)
==============

If you're using asset-based dbt APIs like `load_assets_from_dbt_project`, you usually will not also use the below op-based APIs.

``dagster_dbt`` provides a set of pre-built ops that work with either the CLI or RPC interfaces. For
more advanced use cases, we suggest building your own ops which directly interact with these resources.

.. autoconfigurable:: dbt_run_op

.. autofunction:: dbt_compile_op

.. autofunction:: dbt_ls_op

.. autofunction:: dbt_test_op

.. autofunction:: dbt_snapshot_op

.. autofunction:: dbt_seed_op

.. autofunction:: dbt_docs_generate_op

Resources (dbt Core)
====================

CLI Resource
------------

.. autoclass:: DbtCli

Deprecated CLI Resource
-----------------------

.. autoclass:: DbtCliResource

.. autoclass:: DbtCliOutput

.. autoconfigurable:: dbt_cli_resource
    :annotation: ResourceDefinition

RPC Resources
-------------

.. autoclass:: DbtRpcResource

.. autoclass:: DbtRpcSyncResource

.. autoclass:: DbtRpcOutput

.. autodata:: local_dbt_rpc_resource
    :annotation: ResourceDefinition

.. autoconfigurable:: dbt_rpc_resource
    :annotation: ResourceDefinition

.. autoconfigurable:: dbt_rpc_sync_resource
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

.. autoexception:: DagsterDbtRpcUnexpectedPollOutputError

*****
Utils
*****

.. currentmodule:: dagster_dbt.utils

.. autofunction:: generate_materializations
