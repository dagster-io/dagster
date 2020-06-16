.. currentmodule:: dagster

Pipelines
=========

Pipeline definitions
--------------------
.. autodecorator:: pipeline

.. autoclass:: PipelineDefinition

Dependencies and aliases
------------------------
.. autoclass:: DependencyDefinition

.. autoclass:: MultiDependencyDefinition

.. autoclass:: SolidInvocation

----

Modes
-----

.. autoclass:: ModeDefinition

----

Resources
---------

.. autodecorator:: resource

.. autoclass:: ResourceDefinition
    :members:

.. autoclass:: InitResourceContext
    :members:

----

Logging
-------

.. autodecorator:: logger

.. autoclass:: LoggerDefinition

.. autoclass:: InitLoggerContext

----

Presets
-------

.. autoclass:: PresetDefinition
    :members:

----

Repositories
------------

.. autodata:: repository
  :annotation: RepositoryDefinition

.. autoclass:: RepositoryDefinition
    :members:
