Iceberg (dagster-iceberg)
-------------------------

This library provides an integration with the `Iceberg <https://iceberg.apache.org>`_ table
format.

For more information on getting started, see the `Dagster & Iceberg <https://docs.dagster.io/integrations/libraries/iceberg>`_ documentation.

**Note:** This is a community-supported integration. For support, see the `Dagster Community Integrations repository <https://github.com/dagster-io/community-integrations/tree/main/libraries/dagster-iceberg>`_.


.. currentmodule:: dagster_iceberg

I/O Managers
============
.. autoconfigurable:: dagster_iceberg.io_manager.arrow.PyArrowIcebergIOManager
  :annotation: IOManagerDefinition
.. autoconfigurable:: dagster_iceberg.io_manager.daft.DaftIcebergIOManager
  :annotation: IOManagerDefinition
.. autoconfigurable:: dagster_iceberg.io_manager.pandas.PandasIcebergIOManager
  :annotation: IOManagerDefinition
.. autoconfigurable:: dagster_iceberg.io_manager.polars.PolarsIcebergIOManager
  :annotation: IOManagerDefinition
.. autoconfigurable:: dagster_iceberg.io_manager.spark.SparkIcebergIOManager
  :annotation: IOManagerDefinition

Resources
=========

.. autoconfigurable:: dagster_iceberg.resource.IcebergTableResource
  :annotation: ResourceDefinition

Config
======

.. autoclass:: dagster_iceberg.config.IcebergCatalogConfig

Base Classes
============

.. autoclass:: dagster_iceberg.io_manager.base.IcebergIOManager

.. autoclass:: dagster_iceberg.handler.IcebergBaseTypeHandler
