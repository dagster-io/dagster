Snowflake (dagster-snowflake)
-----------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.

.. currentmodule:: dagster_snowflake

I/O Manager
===========
.. autoconfigurable:: build_snowflake_io_manager
  :annotation: IOManagerDefinition


Resource
========

.. autoconfigurable:: snowflake_resource
  :annotation: ResourceDefinition

.. autoclass:: SnowflakeConnection
  :members:
  :undoc-members:

Ops
===
.. autofunction:: snowflake_op_for_query
