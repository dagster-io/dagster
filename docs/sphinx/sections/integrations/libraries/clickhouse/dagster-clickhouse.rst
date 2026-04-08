############################
dagster-clickhouse library
############################

This library provides an integration with `ClickHouse <https://clickhouse.com>`_ using the native
protocol via `clickhouse-driver <https://clickhouse-driver.readthedocs.io/>`_.

Related guides:

* `Using Dagster with ClickHouse <https://docs.dagster.io/integrations/libraries/clickhouse>`_
* `ClickHouse integration reference <https://docs.dagster.io/integrations/libraries/clickhouse/reference>`_


.. currentmodule:: dagster_clickhouse

*********
Resources
*********

.. autoconfigurable:: ClickhouseResource
  :annotation: ResourceDefinition

*******
I/O manager
*******

.. autoconfigurable:: ClickhouseIOManager
  :annotation: IOManagerDefinition

.. autofunction:: build_clickhouse_io_manager

*****************
Database utilities
*****************

.. autoclass:: ClickhouseDbClient
  :members:

.. autofunction:: format_clickhouse_table_fqn

*********
Component
*********

.. autoclass:: ClickhouseQueryComponent
