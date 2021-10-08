.. currentmodule:: dagster

Ops
===

The foundational unit of computation in Dagster.

-----

Defining ops
------------
.. autodecorator:: op

.. autoclass:: OpDefinition
    :members: configured

-------

Ins & outs
----------------

.. autoclass:: In

.. autoclass:: Out


-------

Execution
---------

.. autoclass:: RetryPolicy

.. autoclass:: Backoff

.. autoclass:: Jitter

-------

.. _events:

Events
------

The objects that can be yielded by the body of ops' compute functions to communicate with the
Dagster framework.

(Note that :py:class:`Failure` and :py:class:`RetryRequested` are intended to be raised from ops rather than yielded.)

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
