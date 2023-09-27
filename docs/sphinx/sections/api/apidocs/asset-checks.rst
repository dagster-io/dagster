.. currentmodule:: dagster

Asset Checks (Experimental)
===========================

Dagster allows you to define and execute checks on your software-defined assets. Each asset check verifies some property of a data asset, e.g. that is has no null values in a particular column.

.. autodecorator:: asset_check

.. autoclass:: AssetCheckResult

.. autoclass:: AssetCheckSpec

.. autoclass:: AssetCheckSeverity

.. autoclass:: AssetCheckKey