.. currentmodule:: dagster

Components
##########

**************************
Building custom Components
**************************

.. autoclass:: Component
    :members:

.. autoclass:: StateBackedComponent
    :members:

.. autoclass:: Resolvable
    :members:

.. autoclass:: ResolutionContext
    :members:

.. autoclass:: Resolver
    :members:

.. autoclass:: Model
    :members:

.. autodecorator:: template_var

Core Models
===========

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


Built-in Components
-------------------

.. autoclass:: DefsFolderComponent

.. autoclass:: DefinitionsComponent

.. autoclass:: UvRunComponent

.. autoclass:: PythonScriptComponent

.. autoclass:: FunctionComponent

.. autoclass:: SqlComponent

.. autoclass:: TemplatedSqlComponent

Loading Components
------------------

.. autofunction:: load_from_defs_folder

Testing Components
------------------

.. currentmodule:: dagster.components.testing

.. autofunction:: create_defs_folder_sandbox

.. autoclass:: DefsFolderSandbox
    :members:


****************
Using Components
****************

.. currentmodule:: dagster

.. autodecorator:: component_instance


.. autoclass:: ComponentLoadContext
   :members:


.. autoclass:: ComponentTree
   :members:


*****************************
Loading Component definitions
*****************************

.. autofunction:: load_from_defs_folder
