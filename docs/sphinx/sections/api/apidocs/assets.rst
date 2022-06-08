.. currentmodule:: dagster

Software-Defined Assets (Experimental)
======================================

Software-defined assets sit on top of the graph/job/op APIs and enable a novel way of constructing Dagster jobs that puts assets at the forefront.

Conceptually, software-defined assets invert the typical relationship between assets and computation. Instead of defining a graph of ops and recording which assets those ops end up materializing, you define a set of assets, each of which knows how to compute its contents from upstream assets.

A software-defined asset combines:
- An asset key, e.g. the name of a table.
- A function, which can be run to compute the contents of the asset.
- A set of upstream assets that are provided as inputs to the function when computing the asset.

.. autodecorator:: asset

.. autoclass:: AssetGroup
   :members:

.. autodecorator:: multi_asset

.. autofunction:: build_assets_job

.. autoclass:: AssetIn

.. autoclass:: SourceAsset

.. autofunction:: assets_from_modules

.. autofunction:: assets_from_current_module

.. autofunction:: assets_from_package_module

.. autofunction:: assets_from_package_name
