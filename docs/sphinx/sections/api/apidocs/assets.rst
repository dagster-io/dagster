.. currentmodule:: dagster

Assets
=======================

An asset is an object in persistent storage, such as a table, file, or persisted machine learning model. An asset definition is a description, in code, of an asset that should exist and how to produce and update that asset.

Asset definitions
-----------------

Refer to the `Asset definitions <https://docs.dagster.io/guides/build/assets/defining-assets>`_ documentation for more information.

.. autodecorator:: asset

.. autoclass:: MaterializeResult

.. autoclass:: AssetSpec

.. autoclass:: AssetsDefinition

.. autoclass:: AssetKey

.. autofunction:: map_asset_specs

Graph-backed asset definitions
------------------------------

Refer to the `Graph-backed asset <https://docs.dagster.io/guides/build/assets/defining-assets#graph-asset>`_ documentation for more information.

.. autodecorator:: graph_asset

.. autodecorator:: graph_multi_asset

Multi-asset definitions
-----------------------

Refer to the `Multi-asset <https://docs.dagster.io/guides/build/assets/defining-assets#multi-asset>`_ documentation for more information.

.. autodecorator:: multi_asset

.. autodecorator:: multi_observable_source_asset

.. autoclass:: AssetOut

Source assets
-------------

Refer to the `External asset dependencies <https://docs.dagster.io/guides/build/assets/external-assets>`_ documentation for more information.

.. autoclass:: SourceAsset

.. autodecorator:: observable_source_asset

.. autoclass:: ObserveResult

Dependencies
------------

.. autoclass:: AssetDep

.. autoclass:: AssetIn

Asset jobs
----------

`Asset jobs <https://docs.dagster.io/guides/build/assets/asset-jobs>`_ enable the automation of asset materializations.  Dagster's `asset selection syntax <https://docs.dagster.io/guides/build/assets/asset-selection-syntax>`_ can be used to select assets and assign them to a job.

.. autofunction:: define_asset_job

.. autoclass:: AssetSelection

Code locations
--------------

Loading assets and asset jobs into a `code location <https://docs.dagster.io/guides/deploy/code-locations/>`_ makes them available to Dagster tools like the UI, CLI, and GraphQL API.

.. autofunction:: load_assets_from_modules

.. autofunction:: load_assets_from_current_module

.. autofunction:: load_assets_from_package_module

.. autofunction:: load_assets_from_package_name

Observations
------------

Refer to the `Asset observation <https://docs.dagster.io/guides/build/assets/metadata-and-tags/asset-observations>`_ documentation for more information.

.. autoclass:: AssetObservation

Declarative Automation
---------------------------------------

Refer to the `Declarative Automation <https://docs.dagster.io/guides/automate/declarative-automation/>`_ documentation for more information.

.. autoclass:: AutomationCondition

.. autoclass:: AutomationResult

.. autoclass:: AutomationConditionSensorDefinition

Asset values
------------

.. autoclass:: AssetValueLoader
