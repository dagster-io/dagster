.. currentmodule:: dagster

Solids
======

The foundational unit of computation in Dagster.

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

Execution
---------

.. autoclass:: RetryPolicy

.. autoclass:: Backoff

.. autoclass:: Jitter

-------

Composing solids
----------------
.. autodecorator:: composite_solid

.. autoclass:: CompositeSolidDefinition
    :members: configured

.. autoclass:: InputMapping

.. autoclass:: OutputMapping

.. autoclass:: ConfigMapping



.. currentmodule:: dagster


.. _events:

Events
------

The objects that can be yielded by the body of solids' compute functions to communicate with the
Dagster framework.

(Note that :py:class:`Failure` and :py:class:`RetryRequested` are intended to be raised from solids rather than yielded.)

Event types
^^^^^^^^^^^

.. autoclass:: Output
    :members:

.. autoclass:: AssetMaterialization
    :members:

.. autoclass:: ExpectationResult
    :members:

.. autoclass:: TypeCheck
    :members:

.. autoclass:: Failure
    :members:

.. autoclass:: RetryRequested

-------

Event metadata
^^^^^^^^^^^^^^

Dagster uses event metadata to communicate arbitrary user-specified metadata about structured
events.

.. autoclass:: EventMetadata
    :members:

.. autoclass:: EventMetadataEntry
    :members:

Metadata types
^^^^^^^^^^^^^^

The type alias for the union of the structured event metadata types is `EventMetadataEntryData`.
This consists of the following data types:

.. autoclass:: JsonMetadataEntryData
    :members:

.. autoclass:: MarkdownMetadataEntryData
    :members:

.. autoclass:: PathMetadataEntryData
    :members:

.. autoclass:: TextMetadataEntryData
    :members:

.. autoclass:: UrlMetadataEntryData
    :members:

.. autoclass:: FloatMetadataEntryData
    :members:

.. autoclass:: IntMetadataEntryData
    :members:

.. autoclass:: PythonArtifactMetadataEntryData
    :members:

-------

Asset key
^^^^^^^^^^^^^^^^

Dagster uses :py:class:`AssetKey` to build an index on :py:class:`Materialization` events.
Assets materialized with an :py:class:`AssetKey` are highlighted in `dagit` on the `Assets`
dashboard.

.. autoclass:: AssetKey
    :members:
