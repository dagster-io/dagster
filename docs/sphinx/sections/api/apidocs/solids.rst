
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
    :noindex:

.. autoclass:: Backoff
    :noindex:

.. autoclass:: Jitter
    :noindex:


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


Events
------

The objects that can be yielded by the body of solids' compute functions to communicate with the
Dagster framework.

(Note that :py:class:`Failure` and :py:class:`RetryRequested` are intended to be raised from solids rather than yielded.)

Event types
^^^^^^^^^^^

.. autoclass:: Output
    :members:
    :noindex:

.. autoclass:: AssetMaterialization
    :members:
    :noindex:

.. autoclass:: ExpectationResult
    :members:
    :noindex:

.. autoclass:: TypeCheck
    :members:
    :noindex:

.. autoclass:: Failure
    :members:
    :noindex:

.. autoclass:: RetryRequested
    :noindex:

-------

Event metadata
^^^^^^^^^^^^^^

Dagster uses event metadata to communicate arbitrary user-specified metadata about structured
events.

.. autoclass:: EventMetadata
    :noindex:
    :members:

.. autoclass:: EventMetadataEntry
    :noindex:
    :members:

Metadata types
^^^^^^^^^^^^^^

The type alias for the union of the structured event metadata types is `EventMetadataEntryData`.
This consists of the following data types:

.. autoclass:: JsonMetadataEntryData
    :noindex:
    :members:

.. autoclass:: MarkdownMetadataEntryData
    :noindex:
    :members:

.. autoclass:: PathMetadataEntryData
    :noindex:
    :members:

.. autoclass:: TextMetadataEntryData
    :noindex:
    :members:

.. autoclass:: UrlMetadataEntryData
    :noindex:
    :members:

.. autoclass:: FloatMetadataEntryData
    :noindex:
    :members:

.. autoclass:: IntMetadataEntryData
    :noindex:
    :members:

.. autoclass:: PythonArtifactMetadataEntryData
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
