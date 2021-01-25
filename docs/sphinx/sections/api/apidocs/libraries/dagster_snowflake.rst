Snowflake (dagster_snowflake)
-----------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse.

Presently, it provides a ``snowflake_resource``, which is a Dagster resource for configuring
Snowflake connections and issuing queries.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.


.. currentmodule:: dagster_snowflake

.. autodata:: snowflake_resource
  :annotation: ResourceDefinition

.. autoclass:: SnowflakeConnection
  :members:
  :undoc-members:
