.. currentmodule:: dagster.components

Components API
==============

Component
---------

.. autoclass:: Component
    :members:

.. autodecorator:: component

ComponentLoadContext
--------------------

.. autoclass:: ComponentLoadContext

.. automethod:: ComponentLoadContext.defs_relative_module_name

.. automethod:: ComponentLoadContext.for_test

.. automethod:: ComponentLoadContext.load_defs

.. automethod:: ComponentLoadContext.load_defs_relative_python_module


Model
-----

.. autoclass:: Model
    :members:

Resolvable
----------

.. autoclass:: Resolvable
    :members:

ResolutionContext
-----------------

.. autoclass:: ResolutionContext
    :members:

Resolver
--------

.. autoclass:: Resolver
    :members: