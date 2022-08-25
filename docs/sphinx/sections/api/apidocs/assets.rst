.. currentmodule:: dagster

Software-Defined Assets
=======================

An asset is an object in persistent storage, such as a table, file, or persisted machine learning model. A software-defined asset is a Dagster object that couples an asset to the function and upstream assets that are used to produce its contents.

.. autodecorator:: asset

.. autoclass:: AssetIn

.. autoclass:: SourceAsset

.. autofunction:: define_asset_job

.. autoclass:: AssetSelection

.. autofunction:: load_assets_from_modules

.. autofunction:: load_assets_from_current_module

.. autofunction:: load_assets_from_package_module

.. autofunction:: load_assets_from_package_name

.. autoclass:: AssetsDefinition

.. autodecorator:: multi_asset

.. autoclass:: AssetOut
