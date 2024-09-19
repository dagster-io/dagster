Snowflake with PySpark (dagster-snowflake-pyspark)
--------------------------------------------------

This library provides an integration with the `Snowflake <https://www.snowflake.com/>`_ data
warehouse and PySpark data processing library.

To use this library, you should first ensure that you have an appropriate `Snowflake user
<https://docs.snowflake.net/manuals/user-guide/admin-user-management.html>`_ configured to access
your data warehouse.

Related Guides:

* `Using Dagster with Snowflake guide <https://docs.dagster.io/integrations/snowflake>`_
* `Snowflake I/O manager reference <https://docs.dagster.io/integrations/snowflake/reference>`_


.. currentmodule:: dagster_snowflake_pyspark

.. autoconfigurable:: SnowflakePySparkIOManager
  :annotation: IOManagerDefinition

.. autoclass:: SnowflakePySparkTypeHandler

Legacy
======

.. autoconfigurable:: snowflake_pyspark_io_manager
  :annotation: IOManagerDefinition