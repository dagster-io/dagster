Snowflake with PySpark (dagster-snowflake-pyspark)
--------------------------------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse and PySpark data processing library.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.

Related Guides:

* `Using Dagster with Snowflake guide </integrations/snowflake>`_


.. currentmodule:: dagster_snowflake_pyspark

.. autoconfigurable:: snowflake_pyspark_io_manager
  :annotation: IOManagerDefinition

.. autoclass:: SnowflakePySparkTypeHandler
