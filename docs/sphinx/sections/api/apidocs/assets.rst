.. currentmodule:: dagster

Software-Defined Assets
=======================

An asset is an object in persistent storage, such as a table, file, or persisted machine learning model. A software-defined asset is a Dagster object that couples an asset to the function and upstream assets that are used to produce its contents.

.. autodecorator:: asset

.. autodecorator:: multi_asset

.. autoclass:: AssetIn

.. autoclass:: SourceAsset

.. autofunction:: materialize

.. autofunction:: define_asset_job

.. autofunction:: load_assets_from_modules

.. autofunction:: load_assets_from_current_module

.. autofunction:: load_assets_from_package_module

.. autofunction:: load_assets_from_package_name
