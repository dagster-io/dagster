Azure (dagster_azure)
---------------------

Utilities for using Azure Storage Accounts with Dagster. This is mostly aimed at Azure Data Lake
Storage Gen 2 (ADLS2) but also contains some utilities for Azure Blob Storage.

|

**NOTE:** This package is incompatible with ``dagster-snowflake``! This is due to a version mismatch
between the underlying ``azure-storage-blob`` package; ``dagster-snowflake`` has a transitive
dependency on an old version, via ``snowflake-connector-python``.


.. currentmodule:: dagster_azure

.. autodata:: dagster_azure.adls2.adls2_resource
  :annotation: ResourceDefinition

.. autoclass:: dagster_azure.adls2.FakeADLS2Resource

.. autodata:: dagster_azure.adls2.adls2_file_cache
  :annotation: ResourceDefinition

.. autodata:: dagster_azure.adls2.adls2_system_storage
  :annotation: SystemStorageDefinition

.. autodata:: dagster_azure.adls2.adls2_intermediate_storage
  :annotation: IntermediateStorageDefinition

.. autoclass:: dagster_azure.blob.AzureBlobComputeLogManager
