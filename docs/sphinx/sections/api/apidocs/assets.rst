.. currentmodule:: dagster

Software-defined Assets
=======================

An asset is an object in persistent storage, such as a table, file, or persisted machine learning model. A Software-defined Asset is a Dagster object that couples an asset to the function and upstream assets that are used to produce its contents.

Assets
------

Refer to the `Software-defined Assets </concepts/assets/software-defined-assets>`_ documentation for more information.

.. autodecorator:: asset

.. autoclass:: MaterializeResult

.. autoclass:: AssetSpec

.. autoclass:: AssetsDefinition

Graph-backed assets
-------------------

Refer to the `Graph-backed asset </concepts/assets/graph-backed-assets>`_ documentation for more information.

.. autodecorator:: graph_asset

.. autodecorator:: graph_multi_asset

Multi-assets
------------

Refer to the `Multi-asset </concepts/assets/multi-assets>`_ documentation for more information.

.. autodecorator:: multi_asset

.. autodecorator:: multi_observable_source_asset

.. autoclass:: AssetOut

Source assets
-------------

Refer to the `External asset dependencies </concepts/assets/software-defined-assets#defining-external-asset-dependencies>`_ documentation for more information.

.. autoclass:: SourceAsset

.. autodecorator:: observable_source_asset

.. autoclass:: ObserveResult

External assets
---------------

Refer to the `External assets </concepts/assets/external-assets>`_ documentation for more information.

.. autofunction:: external_assets_from_specs

Dependencies
------------

.. autoclass:: AssetDep

.. autoclass:: AssetIn

Asset jobs
----------

`Asset jobs </concepts/assets/asset-jobs>`_ enable the automation of asset materializations.  Dagster's `asset selection syntax </concepts/assets/asset-selection-syntax>`_ can be used to select assets and assign them to a job. 

.. autofunction:: define_asset_job

.. autoclass:: AssetSelection

Code locations
--------------

Loading assets and asset jobs into a `code location </concepts/code-locations>`_ makes them available to Dagster tools like the UI, CLI, and GraphQL API.

.. autofunction:: load_assets_from_modules

.. autofunction:: load_assets_from_current_module

.. autofunction:: load_assets_from_package_module

.. autofunction:: load_assets_from_package_name

Observations
------------

Refer to the `Asset observation </concepts/assets/asset-observations>`_ documentation for more information.

.. autoclass:: AssetObservation

Auto-materialize and freshness policies
---------------------------------------

Refer to the `Auto-materialize policies </concepts/assets/asset-auto-execution>`_ documentation for more information.

.. autoclass:: AutoMaterializePolicy

.. autoclass:: AutoMaterializeRule

.. autoclass:: AutoMaterializeSensorDefinition

.. autoclass:: AssetCondition

.. autoclass:: FreshnessPolicy

Asset values
------------

.. autoclass:: AssetValueLoader
