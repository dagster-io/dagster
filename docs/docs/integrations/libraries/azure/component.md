---
title: Azure Components
sidebar_label: Components
sidebar_position: 1
description: Configuration-driven Azure resources using Dagster Components.
tags: [dagster-supported, azure, components]
---

<p>{frontMatter.description}</p>

The `dagster-azure` library provides a set of components that allow you to configure Azure resources directly in YAML. These components wrap existing `dagster-azure` resources, enabling faster setup and declarative infrastructure.

## Installation

<PackageInstallInstructions packageName="dagster-azure" />

## Credentials configuration

Unlike other libraries, Azure components utilize **Discriminated Unions** for credentials. This means you specify the `credential_type` inline within your YAML configuration to select the authentication method (SAS Token, Shared Key, DefaultCredential, or Anonymous).

Supported credential types:
- **`sas`**: Uses a Shared Access Signature token.
- **`key`**: Uses a Storage Account Key.
- **`default`**: Uses the environment's `DefaultAzureCredential` (supports Azure CLI, Managed Identity, etc.).
- **`anonymous`**: For public resources.

## Service Components

### Azure Blob Storage

Components for interacting with Azure Blob Storage.

- **`AzureBlobStorageResourceComponent`**: Provides a standard `AzureBlobStorageResource`.

### Azure Data Lake Storage Gen2 (ADLS2)

Components for interacting with ADLS2.

- **`ADLS2ResourceComponent`**: Provides an `ADLS2Resource`.

## Examples

### Blob Storage with SAS Token Connect using a SAS token.

```yaml
type: dagster_azure.AzureBlobStorageResourceComponent
attributes:
  account_url: "[https://myaccount.blob.core.windows.net](https://myaccount.blob.core.windows.net)"
  credential:
    credential_type: sas
    token: "{{ env.AZURE_SAS_TOKEN }}"
  resource_key: blob_storage
```
### ADLS2 with Shared Key Connect using a Storage Account Key.

```yaml
type: dagster_azure.ADLS2ResourceComponent
attributes:
  storage_account: mystorageaccount
  credential:
    credential_type: key
    storage_account_key: "{{ env.AZURE_STORAGE_KEY }}"
  resource_key: adls2
```
