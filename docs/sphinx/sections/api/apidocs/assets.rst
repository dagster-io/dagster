.. currentmodule:: dagster

Software-Defined Assets
=======================

An asset is an object in persistent storage, such as a table, file, or persisted machine learning model. A software-defined asset is a Dagster object that couples an asset to the function and upstream assets that are used to produce its contents.

.. autodecorator:: asset

.. autoclass:: MaterializeResult

.. autoclass:: AssetSpec

.. autofunction:: external_assets_from_specs

.. autoclass:: AssetDep

.. autoclass:: AssetIn

.. autoclass:: SourceAsset

.. autodecorator:: observable_source_asset

.. autoclass:: ObserveResult

.. autofunction:: define_asset_job

.. autoclass:: AssetSelection

.. autoclass:: FreshnessPolicy

.. autoclass:: AutoMaterializePolicy

.. autoclass:: AutoMaterializeRule

.. autoclass:: AutoMaterializeSensorDefinition

.. autofunction:: load_assets_from_modules

.. autofunction:: load_assets_from_current_module

.. autofunction:: load_assets_from_package_module

.. autofunction:: load_assets_from_package_name

.. autoclass:: AssetsDefinition

.. autodecorator:: multi_asset

.. autodecorator:: multi_observable_source_asset

.. autodecorator:: graph_asset

.. autodecorator:: graph_multi_asset

.. autoclass:: AssetOut

.. autoclass:: AssetValueLoader
