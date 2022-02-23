.. currentmodule:: dagster

[Legacy] Solids
===============

As of Dagster 0.13.0, we recommend `Ops` as an alternative to `Solids`. They can generally be used
interchangeably.

-----

Defining solids
---------------
.. autodecorator:: solid

.. autoclass:: SolidDefinition
    :members: configured

-------

Inputs & outputs
----------------

.. autoclass:: InputDefinition

.. autoclass:: OutputDefinition


-------

Retries
-------


.. autoclass:: RetryPolicy
    :noindex:

.. autoclass:: Backoff
    :noindex:

.. autoclass:: Jitter
    :noindex:

Execution
---------

.. autofunction:: execute_solid

.. autofunction:: execute_solid_within_pipeline

.. autofunction:: execute_solids_within_pipeline

.. autoclass:: SolidExecutionResult
   :members:
   :inherited-members:

.. autoclass:: CompositeSolidExecutionResult
   :members:
   :inherited-members:


Execution context
-----------------
.. currentmodule:: dagster

.. autoclass:: SolidExecutionContext
   :members:
   :inherited-members:

.. autofunction:: build_solid_context

-------

Composing solids
----------------
.. autodecorator:: composite_solid

.. autoclass:: CompositeSolidDefinition
    :members: configured

.. autoclass:: InputMapping

.. autoclass:: OutputMapping

.. autoclass:: ConfigMapping
    :noindex:



.. currentmodule:: dagster


.. _solid_events:

Events
------

The objects that can be yielded by the body of solids' compute functions to communicate with the
Dagster framework.

(Note that :py:class:`Failure` and :py:class:`RetryRequested` are intended to be raised from solids rather than yielded.)

Event types
^^^^^^^^^^^

.. autoclass:: Output
    :noindex:
    :members:

.. autoclass:: AssetMaterialization
    :noindex:
    :members:

.. autoclass:: ExpectationResult
    :noindex:
    :members:

.. autoclass:: TypeCheck
    :noindex:
    :members:

.. autoclass:: Failure
    :noindex:
    :members:

.. autoclass:: RetryRequested
    :noindex:

-------

Metadata
^^^^^^^^^^^^^^

Dagster uses metadata to communicate arbitrary user-specified metadata about structured
events.

.. autoclass:: MetadataValue
    :noindex:
    :members:

.. autoclass:: MetadataEntry
    :noindex:
    :members:

Metadata types
^^^^^^^^^^^^^^

All metadata types inherit from `MetadataValue`. The following types are defined:

.. autoclass:: DagsterAssetMetadataValue
    :noindex:
    :members:

.. autoclass:: DagsterPipelineRunMetadataValue
    :noindex:
    :members:

.. autoclass:: FloatMetadataValue
    :noindex:
    :members:

.. autoclass:: IntMetadataValue
    :noindex:
    :members:

.. autoclass:: JsonMetadataValue
    :noindex:
    :members:

.. autoclass:: MarkdownMetadataValue
    :noindex:
    :members:

.. autoclass:: PathMetadataValue
    :noindex:
    :members:

.. autoclass:: PythonArtifactMetadataValue
    :noindex:
    :members:

.. autoclass:: TableMetadataValue
    :noindex:
    :members:

.. autoclass:: TableSchemaMetadataValue
    :noindex:
    :members:

.. autoclass:: TextMetadataValue
    :noindex:
    :members:

.. autoclass:: UrlMetadataValue
    :noindex:
    :members:

-------

Asset key
^^^^^^^^^^^^^^^^

Dagster uses :py:class:`AssetKey` to build an index on :py:class:`Materialization` events.
Assets materialized with an :py:class:`AssetKey` are highlighted in `dagit` on the `Assets`
dashboard.

.. autoclass:: AssetKey
    :noindex:
    :members:
