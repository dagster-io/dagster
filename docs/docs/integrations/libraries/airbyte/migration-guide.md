---
title: Migrating from Legacy Airbyte Resources
sidebar_label: Migration Guide
description: Learn how to migrate from legacy Airbyte resources to the new AirbyteWorkspace and AirbyteCloudWorkspace.
tags: [dagster-supported, migration, etl]
---

# Migrating from Legacy Airbyte Resources

The `dagster-airbyte` integration has been significantly improved with new resource implementations that provide better API compatibility, cleaner configuration, and enhanced functionality. This guide will help you migrate from the legacy resources to the new ones.

## Overview of Changes

The legacy Airbyte integration used:

- `AirbyteResource` / `airbyte_resource` for OSS Airbyte
- `AirbyteCloudResource` / `airbyte_cloud_resource` for Airbyte Cloud
- `load_assets_from_airbyte_instance` for loading assets

The new integration uses:

- `AirbyteWorkspace` for OSS Airbyte
- `AirbyteCloudWorkspace` for Airbyte Cloud
- `build_airbyte_assets_definitions` for loading assets

## Key Benefits of the New Resources

1. **Better API Compatibility**: Properly separates REST API and Configuration API endpoints
2. **Cleaner Configuration**: More intuitive parameter names and structure
3. **Enhanced Features**: Better asset metadata, improved error handling
4. **Future-Proof**: Active development and maintenance

## Migration for OSS Airbyte

### Legacy Implementation

```python
from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance
import dagster as dg

# Old way (deprecated)
airbyte_resource = AirbyteResource(
    host="localhost",
    port="8000",
    username="airbyte",
    password=dg.EnvVar("AIRBYTE_PASSWORD"),
)

airbyte_assets = load_assets_from_airbyte_instance(
    airbyte=airbyte_resource
)

defs = dg.Definitions(
    assets=[airbyte_assets],
)
```

### New Implementation

```python
from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions
import dagster as dg

# New way (recommended)
airbyte_workspace = AirbyteWorkspace(
    rest_api_base_url="http://localhost:8000/api/public/v1",
    configuration_api_base_url="http://localhost:8000/api/v1",
    workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
    username="airbyte",
    password=dg.EnvVar("AIRBYTE_PASSWORD"),
)

airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

defs = dg.Definitions(
    assets=airbyte_assets,
    resources={"airbyte": airbyte_workspace},
)
```

### Key Changes for OSS Migration

1. **API Endpoints**: Must specify both REST API (`/api/public/v1`) and Configuration API (`/api/v1`) URLs
2. **Workspace ID**: Required parameter - get this from your Airbyte instance
3. **Configuration**: More explicit URL configuration instead of host/port
4. **Asset Loading**: Use `build_airbyte_assets_definitions` instead of `load_assets_from_airbyte_instance`

## Migration for Airbyte Cloud

### Legacy Implementation

```python
from dagster_airbyte import AirbyteCloudResource, load_assets_from_airbyte_instance
import dagster as dg

# Old way (deprecated)
airbyte_cloud_resource = AirbyteCloudResource(
    client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
)

airbyte_assets = load_assets_from_airbyte_instance(
    airbyte=airbyte_cloud_resource
)

defs = dg.Definitions(
    assets=[airbyte_assets],
)
```

### New Implementation

```python
from dagster_airbyte import AirbyteCloudWorkspace, build_airbyte_assets_definitions
import dagster as dg

# New way (recommended)
airbyte_workspace = AirbyteCloudWorkspace(
    workspace_id=dg.EnvVar("AIRBYTE_CLOUD_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
)

airbyte_assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)

defs = dg.Definitions(
    assets=airbyte_assets,
    resources={"airbyte": airbyte_workspace},
)
```

### Key Changes for Cloud Migration

1. **Workspace ID**: Now required - get this from your Airbyte Cloud workspace
2. **Asset Loading**: Use `build_airbyte_assets_definitions` instead of `load_assets_from_airbyte_instance`
3. **Resource Definition**: Include the workspace in your Definitions

## Configuration Mapping

### Environment Variables

You'll need to update your environment variables:

**For OSS Airbyte:**

```bash
# Legacy
AIRBYTE_HOST=localhost
AIRBYTE_PORT=8000
AIRBYTE_USERNAME=airbyte
AIRBYTE_PASSWORD=your_password

# New
AIRBYTE_REST_API_BASE_URL=http://localhost:8000/api/public/v1
AIRBYTE_CONFIGURATION_API_BASE_URL=http://localhost:8000/api/v1
AIRBYTE_WORKSPACE_ID=your_workspace_id
AIRBYTE_USERNAME=airbyte
AIRBYTE_PASSWORD=your_password
```

**For Airbyte Cloud:**

```bash
# Legacy
AIRBYTE_CLIENT_ID=your_client_id
AIRBYTE_CLIENT_SECRET=your_client_secret

# New
AIRBYTE_CLOUD_WORKSPACE_ID=your_workspace_id
AIRBYTE_CLIENT_ID=your_client_id
AIRBYTE_CLIENT_SECRET=your_client_secret
```

## Common Migration Steps

1. **Update Imports**: Change from legacy resource imports to new workspace imports
2. **Update Configuration**: Use the new configuration parameters
3. **Get Workspace ID**: Retrieve your workspace ID from Airbyte
4. **Update Asset Loading**: Replace `load_assets_from_airbyte_instance` with `build_airbyte_assets_definitions`
5. **Test Connection**: Verify the new configuration works with your Airbyte instance

## Getting Your Workspace ID

### For OSS Airbyte

1. Access your Airbyte instance at `http://your-host:port`
2. Go to Settings → General
3. Copy the Workspace ID

### For Airbyte Cloud

1. Log into [Airbyte Cloud](https://cloud.airbyte.com)
2. Go to your workspace settings
3. Copy the Workspace ID

## Troubleshooting

### Connection Issues

- **OSS Airbyte**: Ensure you're using the correct API endpoints (`/api/public/v1` for REST, `/api/v1` for Configuration)
- **Authentication**: Verify credentials and workspace ID are correct
- **Network**: Check that Airbyte instance is accessible from Dagster

### Asset Loading Issues

- **Workspace ID**: Ensure the workspace ID matches your Airbyte workspace
- **Permissions**: Verify your credentials have access to the workspace
- **Connections**: Check that connections exist in the specified workspace

## Getting Help

If you encounter issues during migration:

1. Check the [Airbyte Component documentation](/integrations/libraries/airbyte/airbyte-component) for the latest patterns
2. Review the [API documentation](/api/libraries/dagster-airbyte) for detailed parameter information
3. Look at the example code in the docs snippets directory
