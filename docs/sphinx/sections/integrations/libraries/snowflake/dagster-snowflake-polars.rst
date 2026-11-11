################################
dagster-snowflake-polars library
################################

This library provides an integration with Snowflake and Polars, allowing you to use Polars DataFrames with Snowflake storage.

.. currentmodule:: dagster_snowflake_polars

************
Installation
************

The Snowflake Polars integration uses the ADBC driver manager and the
Snowflake ADBC driver.

The Python driver manager is installed automatically as a dependency of
``dagster-snowflake-polars``. The native Snowflake driver must be installed
separately using the Driver Foundry CLI:

.. code-block:: bash

    uv tool install dbc
    dbc install snowflake

Activate the Python virtual environment used by the Dagster process before
running ``dbc install snowflake``. The CLI detects the active environment and
installs the native driver there.

***********
I/O manager
***********

.. autofunction:: snowflake_polars_io_manager

.. autoclass:: SnowflakePolarsIOManager
    :members:

************
Type handler
************

.. autoclass:: SnowflakePolarsTypeHandler
    :members: