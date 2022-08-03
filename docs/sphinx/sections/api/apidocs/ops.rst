.. currentmodule:: dagster

Ops
===

The foundational unit of computation in Dagster.

-----

Defining ops
------------
.. autodecorator:: op

.. autoclass:: OpDefinition
   :members:
   :undoc-members:

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

Dagster uses metadata to communicate arbitrary user-specified metadata about structured
events.

.. autoclass:: MetadataValue
    :members:

.. autoclass:: MetadataEntry
    :members:

Metadata types
^^^^^^^^^^^^^^

All metadata types inherit from `MetadataValue`. The following types are defined:

.. autoclass:: DagsterAssetMetadataValue
    :members:

.. autoclass:: DagsterRunMetadataValue
    :members:

.. autoclass:: FloatMetadataValue
    :members:

.. autoclass:: IntMetadataValue
    :members:

.. autoclass:: JsonMetadataValue
    :members:

.. autoclass:: MarkdownMetadataValue
    :members:

.. autoclass:: PathMetadataValue
    :members:

.. autoclass:: PythonArtifactMetadataValue
    :members:

.. autoclass:: TableMetadataValue
    :members:

.. autoclass:: TableSchemaMetadataValue
    :members:

.. autoclass:: TextMetadataValue
    :members:

.. autoclass:: UrlMetadataValue
    :members:

Tables
^^^^^^

These APIs provide the ability to express table schemas (`TableSchema`) and table rows/records (`TableRecord`) in Dagster. Currently the only use case for `TableSchemas` and `TableRecords` is to wrap them in their corresponding metadata classes :py:class:`TableMetadataValue` and :py:class:`TableSchemaMetadataValue` for attachment to events or Dagster types.

.. autoclass:: TableRecord

.. autoclass:: TableSchema

.. autoclass:: TableConstraints

.. autoclass:: TableColumn

.. autoclass:: TableColumnConstraints

-------

Asset key
^^^^^^^^^^^^^^^^

Dagster uses :py:class:`AssetKey` to build an index on :py:class:`Materialization` events.
Assets materialized with an :py:class:`AssetKey` are highlighted in `dagit` on the `Assets`
dashboard.

.. autoclass:: AssetKey
    :members:
