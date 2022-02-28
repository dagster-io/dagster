.. currentmodule:: dagster

Tables
======

These APIs provide the ability to express table schemas (`TableSchema`) and table rows/records (`TableRecord`) in Dagster. Currently the only use case for `TableSchemas` and `TableRecords` is to wrap them in their corresponding metadata classes :py:class:`TableMetadataValue` and :py:class:`TableSchemaMetadataValue` for attachment to events or Dagster types.

.. autoclass:: TableRecord

.. autoclass:: TableSchema

.. autoclass:: TableConstraints

.. autoclass:: TableColumn

.. autoclass:: TableColumnConstraints
