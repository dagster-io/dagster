Snowflake with Pandas (dagster-snowflake-pandas)
------------------------------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse and Pandas data processing library.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.

Related Guides:

* `Using Dagster with Snowflake guide <https://docs.dagster.io/integrations/snowflake>`_
* `Snowflake I/O manager reference <https://docs.dagster.io/integrations/snowflake/reference>`_

.. currentmodule:: dagster_snowflake_pandas

.. autoconfigurable:: SnowflakePandasIOManager
  :annotation: IOManagerDefinition

.. autoclass:: SnowflakePandasTypeHandler


Legacy
======

.. autoconfigurable:: snowflake_pandas_io_manager
  :annotation: IOManagerDefinition
