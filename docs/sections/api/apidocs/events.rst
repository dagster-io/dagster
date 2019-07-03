.. currentmodule:: dagster

Events
======

The types of objects that can be yielded during Solid compute functions to communicate
rich information to Dagster.

.. autoclass:: Output
    :members:

.. autoclass:: Materialization
    :members:

.. autoclass:: ExpectationResult
    :members:

.. autoclass:: TypeCheck
    :members:

.. autoclass:: Failure
    :members:

-------

Metadata
--------

.. autoclass:: EventMetadataEntry
    :members:

.. autoclass:: TextMetadataEntryData
    :members:

.. autoclass:: UrlMetadataEntryData
    :members:

.. autoclass:: PathMetadataEntryData
    :members:

.. autoclass:: JsonMetadataEntryData
    :members:
