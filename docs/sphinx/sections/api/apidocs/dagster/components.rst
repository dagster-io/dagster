.. currentmodule:: dagster.components

Components
==========

Using Components
----------------

.. autodecorator:: component


.. autoclass:: ComponentLoadContext
    :members:


Building Components
-------------------

.. autoclass:: Component
    :members:


.. autoclass:: Resolvable
    :members:


.. autoclass:: ResolutionContext
    :members:


.. autoclass:: Resolver
    :members:


.. autoclass:: Model
    :members:


Core Models
-----------

These Annotated TypeAliases can be used when defining custom Components for
common dagster types.


    AssetAttributesModel as AssetAttributesModel,
    AssetPostProcessorModel as AssetPostProcessorModel,
    ResolvedAssetCheckSpec as ResolvedAssetCheckSpec,
    ResolvedAssetKey as ResolvedAssetKey,
    ResolvedAssetSpec as ResolvedAssetSpec,
