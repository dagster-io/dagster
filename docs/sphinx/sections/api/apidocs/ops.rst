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

.. autoclass:: AssetMaterialization

.. autoclass:: ExpectationResult

.. autoclass:: TypeCheck

.. autoclass:: Failure

.. autoclass:: RetryRequested

-------

Event metadata
^^^^^^^^^^^^^^

Dagster uses metadata to communicate arbitrary user-specified metadata about structured
events.

.. autoclass:: MetadataValue

.. autoclass:: MetadataEntry

Metadata types
^^^^^^^^^^^^^^

All metadata types inherit from `MetadataValue`. The following types are defined:

.. autoclass:: DagsterAssetMetadataValue

.. autoclass:: DagsterRunMetadataValue

.. autoclass:: FloatMetadataValue

.. autoclass:: IntMetadataValue

.. autoclass:: JsonMetadataValue

.. autoclass:: MarkdownMetadataValue

.. autoclass:: PathMetadataValue

.. autoclass:: NotebookMetadataValue

.. autoclass:: PythonArtifactMetadataValue

.. autoclass:: TableMetadataValue

.. autoclass:: TableSchemaMetadataValue

.. autoclass:: TextMetadataValue

.. autoclass:: TimestampMetadataValue

.. autoclass:: UrlMetadataValue

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
Assets materialized with an :py:class:`AssetKey` are highlighted in the Dagster UI on the `Assets`
dashboard.

.. autoclass:: AssetKey
