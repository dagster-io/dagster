.. currentmodule:: dagster

Metadata
========

Dagster uses metadata to communicate arbitrary user-specified metadata about structured
events.

Refer to the `Metadata <https://docs.dagster.io/concepts/metadata-tags>`_ documentation for more information.

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

.. autoclass:: TableColumnLineageMetadataValue

.. autoclass:: TableMetadataValue

.. autoclass:: TableSchemaMetadataValue

.. autoclass:: TextMetadataValue

.. autoclass:: TimestampMetadataValue

.. autoclass:: UrlMetadataValue

.. autoclass:: CodeReferencesMetadataValue

Tables
^^^^^^

These APIs provide the ability to express column schemas (`TableSchema`), rows/records (`TableRecord`), and column lineage (`TableColumnLineage`) in Dagster as metadata.

.. autoclass:: TableRecord

.. autoclass:: TableSchema

.. autoclass:: TableConstraints

.. autoclass:: TableColumn

.. autoclass:: TableColumnConstraints

.. autoclass:: TableColumnLineage

.. autoclass:: TableColumnDep

Code references
^^^^^^^^^^^^^^^

The following functions are used to attach source code references to your assets.
For more information, refer to the `Linking to asset definition code with code references <https://docs.dagster.io/guides/dagster/code-references>`_ guide.


.. autofunction:: with_source_code_references

.. autofunction:: link_code_references_to_git

.. autoclass:: FilePathMapping

.. autoclass:: AnchorBasedFilePathMapping
