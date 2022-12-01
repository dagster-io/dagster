Snowflake with Pandas (dagster-snowflake-pandas)
------------------------------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse and Pandas data processing library.

`Using Dagster with Snowflake guide </integrations/snowflake>`_.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.


.. currentmodule:: dagster_snowflake_pandas

.. autoconfigurable:: snowflake_pandas_io_manager
  :annotation: IOManagerDefinition

.. autoclass:: SnowflakePandasTypeHandler
