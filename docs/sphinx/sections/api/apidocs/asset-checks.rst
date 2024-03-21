.. currentmodule:: dagster

Asset Checks (Experimental)
===========================

Dagster allows you to define and execute checks on your software-defined assets. Each asset check verifies some property of a data asset, e.g. that is has no null values in a particular column.

.. autodecorator:: asset_check

.. autoclass:: AssetCheckResult

.. autoclass:: AssetCheckSpec

.. autoclass:: AssetCheckSeverity

.. autoclass:: AssetCheckKey

.. autofunction:: load_asset_checks_from_modules

.. autofunction:: load_asset_checks_from_current_module

.. autofunction:: load_asset_checks_from_package_module

.. autofunction:: load_asset_checks_from_package_name

.. autoclass:: AssetChecksDefinition

.. autofunction:: build_freshness_checks_for_non_partitioned_assets

.. autofunction:: build_freshness_checks_for_time_window_partitioned_assets

.. autofunction:: build_sensor_for_freshness_checks 
    