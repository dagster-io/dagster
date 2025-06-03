.. currentmodule:: dagster

Components
==========

Using Components
----------------

.. autodecorator:: component_instance


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
common Dagster types.


.. py:data:: ResolvedAssetKey
    :type: Annotated[AssetKey, ...]

    Allows resolving to an AssetKey via a YAML-friendly schema.

.. py:data:: ResolvedAssetSpec
    :type: Annotated[AssetSpec, ...]

    Allows resolving to an AssetSpec via a YAML-friendly schema.

.. py:data:: AssetAttributesModel

    A pydantic modeling of all the attributes of an AssetSpec that can be set before the definition is created.

.. py:data:: ResolvedAssetCheckSpec
    :type: Annotated[AssetCheckSpec, ...]

    Allows resolving to an AssetCheckSpec via a YAML-friendly schema.

.. autoclass:: AssetPostProcessorModel
