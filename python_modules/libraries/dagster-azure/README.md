# dagster-azure

Utilities for using Azure Storage Accounts with Dagster. This is mostly aimed at Azure Data Lake Storage Gen 2 (ADLS2) but also contains some utilities for Azure Blob Storage.

**This package is incompatible with dagster-snowflake!** This is due to a version mismatch between the underlying azure-storage-blob package (dagster-snowflake has a transitive dependency on an old version, via snowflake-connector-python).

## Utilities

- ADLS2 file cache (see the `dagster_azure.adls2.adls2_file_cache` resource)
- The `dagster_azure.adls2.adls2_resource` providing solids access to an ADLS2 client
- Persistent storage using ADLS2 (see `dagster_azure.adls2.adls2_system_storage`)
- Log management using Azure Blob Storage (also compatible with ADLS - see `dagster_azure.blob.AzureBlobComputeLogManager`
- Fake clients for use in tests (see `dagster_azure.adls2.FakeADLS2Resource`)
