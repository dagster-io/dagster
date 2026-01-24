dagster-dbt library
###################

Dagster orchestrates `dbt <https://www.getdbt.com/>`_ alongside other technologies, so you can combine dbt with Spark, Python,
and other tools in a single workflow. Dagster's software-defined asset abstractions make it simple to define
data assets that depend on specific dbt models, or define the computation required to compute
the sources that your dbt models depend on.

For more information on using the dbt and dbt Cloud integrations, see the `Dagster & dbt <https://docs.dagster.io/integrations/libraries/dbt>`_ and
`Dagster & dbt Cloud <https://docs.dagster.io/integrations/libraries/dbt/dbt-cloud>`_ docs.

.. currentmodule:: dagster_dbt

*******************
DbtProjectComponent
*******************

.. autoclass:: DbtProjectComponent
    :members:

To use the dbt component, see the `dbt component integration guide <https://docs.dagster.io/integrations/libraries/dbt>`_.

Component YAML
==============

When you scaffold a dbt component definition, the following ``defs.yaml`` configuration file will be created:

.. literalinclude:: ../../../../../../examples/docs_snippets/docs_snippets/guides/components/integrations/dbt-component/7-component.yaml
    :language: yaml

*****************
DbtCloudComponent
*****************

.. autoclass:: DbtCloudComponent
    :members:

***********
dagster-dbt
***********

.. click:: dagster_dbt.cli.app:project_app_typer_click_object
    :prog: dagster-dbt project
    :nested: full

********
dbt Core
********

Here, we provide interfaces to manage dbt projects invoked by the local dbt command line interface
(dbt CLI).

Assets (dbt Core)
=================

.. autodecorator:: dbt_assets

.. autoclass:: DagsterDbtTranslator

.. autoclass:: DagsterDbtTranslatorSettings

.. autoclass:: DbtManifestAssetSelection

.. autofunction:: build_dbt_asset_selection

.. autofunction:: build_schedule_from_dbt_selection

.. autofunction:: get_asset_key_for_model

.. autofunction:: get_asset_key_for_source

.. autofunction:: get_asset_keys_by_output_name_for_source

.. autoclass:: DbtProject

Asset Checks (dbt Core)
=======================

.. autofunction:: build_freshness_checks_from_dbt_assets

Resources (dbt Core)
====================

CLI Resource
------------

.. autoclass:: DbtCliResource

.. autoclass:: DbtCliInvocation

.. autoclass:: dagster_dbt.core.dbt_cli_invocation.DbtEventIterator

.. autoclass:: DbtCliEventMessage

************
dbt Cloud v2
************

Updated interfaces to manage dbt projects invoked by the hosted dbt Cloud service.

Assets (dbt Cloud v2)
=====================

.. autodecorator:: dbt_cloud_assets

Resources (dbt Cloud v2)
========================

.. autoclass:: DbtCloudCredentials

.. autoclass:: DbtCloudWorkspace

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

.. autoclass:: DbtCloudClientResource

Deprecated (dbt Cloud)
----------------------

.. autoconfigurable:: dbt_cloud_resource
    :annotation: ResourceDefinition

******
Errors
******

.. autoexception:: DagsterDbtError

.. autoexception:: DagsterDbtCliRuntimeError

*****
Utils
*****

.. autofunction:: default_group_from_dbt_resource_props

.. autofunction:: group_from_dbt_resource_props_fallback_to_directory

.. autofunction:: default_metadata_from_dbt_resource_props
