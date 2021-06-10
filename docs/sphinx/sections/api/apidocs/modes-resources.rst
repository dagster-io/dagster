.. currentmodule:: dagster

Modes & Resources
=================

Modes
-----

.. autoclass:: ModeDefinition

----

Resources
---------

.. autodecorator:: resource

.. autoclass:: ResourceDefinition
    :members: hardcoded_resource, mock_resource, none_resource, configured

.. autoclass:: InitResourceContext
    :members:

.. autofunction:: make_values_resource

.. autofunction:: build_init_resource_context
