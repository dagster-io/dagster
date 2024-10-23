Snowflake (dagster-snowflake)
-----------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.

Related Guides:

* `Using Dagster with Snowflake <https://docs.dagster.io/integrations/snowflake>`_
* `Snowflake I/O manager reference <https://docs.dagster.io/integrations/snowflake/reference>`_
* `Transitioning data pipelines from development to production <https://docs.dagster.io/guides/dagster/transitioning-data-pipelines-from-development-to-production>`_
* `Testing against production with Dagster+ Branch Deployments <https://docs.dagster.io/guides/dagster/branch_deployments>`_


.. currentmodule:: dagster_snowflake

I/O Manager
===========
.. autoconfigurable:: SnowflakeIOManager
  :annotation: IOManagerDefinition

Resource
========

.. autoconfigurable:: SnowflakeResource
  :annotation: ResourceDefinition

.. autoclass:: SnowflakeConnection
  :members:

Data Freshness 
==============

.. autofunction:: fetch_last_updated_timestamps

Ops
===
.. autofunction:: snowflake_op_for_query


Legacy
=======

.. autoconfigurable:: build_snowflake_io_manager
  :annotation: IOManagerDefinition

.. autoconfigurable:: snowflake_resource
  :annotation: ResourceDefinition
