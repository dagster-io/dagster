.. currentmodule:: dagster

Asset Checks
===========================

With Dagster, you can define and execute checks on your software-defined assets. Each asset check verifies some property of a data asset, for example that it has no null values in a particular column.

.. autodecorator:: asset_check

.. autoclass:: AssetCheckResult

.. autoclass:: AssetCheckSpec

.. autoclass:: AssetCheckSeverity

.. autoclass:: AssetCheckKey

.. autodecorator:: multi_asset_check

.. autofunction:: load_asset_checks_from_modules

.. autofunction:: load_asset_checks_from_current_module

.. autofunction:: load_asset_checks_from_package_module

.. autofunction:: load_asset_checks_from_package_name

.. autoclass:: AssetChecksDefinition

.. autofunction:: build_last_update_freshness_checks 

.. autofunction:: build_time_partition_freshness_checks 

.. autofunction:: build_sensor_for_freshness_checks 

.. autofunction:: build_column_schema_change_checks

.. autofunction:: build_metadata_bounds_checks