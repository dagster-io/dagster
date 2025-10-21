---
title: Dagster & Airbyte OSS
sidebar_label: Airbyte OSS
description: Using this integration, you can trigger Airbyte syncs and orchestrate your Airbyte connections from within Dagster, making it easy to chain an Airbyte sync with upstream or downstream steps in your workflow.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-airbyte
pypi: https://pypi.org/project/dagster-airbyte/
sidebar_custom_props:
  logo: images/integrations/airbyte.svg
partnerlink: https://airbyte.com/tutorials/orchestrate-data-ingestion-and-transformation-pipelines
---

<p>{frontMatter.description}</p>

:::note

For new projects, we recommend using the new [Airbyte Workspace Component](/integrations/libraries/airbyte/airbyte-component) which provides a more streamlined configuration experience.

:::

## Installation

<PackageInstallInstructions packageName="dagster-airbyte" />

## Example

<CodeExample path="docs_snippets/docs_snippets/integrations/airbyte.py" language="python" />

## Configuration

The `AirbyteWorkspace` resource requires both a REST API URL and Configuration API URL:

- **REST API URL**: `http(s)://<your-airbyte-host>/api/public/v1`
- **Configuration API URL**: `http(s)://<your-airbyte-host>/api/v1`

### Authentication Methods

#### Basic Authentication

```python
from dagster_airbyte import AirbyteWorkspace
import dagster as dg

airbyte_workspace = AirbyteWorkspace(
    rest_api_base_url="http://localhost:8000/api/public/v1",
    configuration_api_base_url="http://localhost:8000/api/v1", 
    workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
    username=dg.EnvVar("AIRBYTE_USERNAME"),
    password=dg.EnvVar("AIRBYTE_PASSWORD"),
)
```

#### OAuth Client Credentials

```python
airbyte_workspace = AirbyteWorkspace(
    rest_api_base_url="http://localhost:8000/api/public/v1",
    configuration_api_base_url="http://localhost:8000/api/v1",
    workspace_id=dg.EnvVar("AIRBYTE_WORKSPACE_ID"),
    client_id=dg.EnvVar("AIRBYTE_CLIENT_ID"),
    client_secret=dg.EnvVar("AIRBYTE_CLIENT_SECRET"),
)
```

### Migration from Legacy Resources

If you're using the legacy `AirbyteResource` or `airbyte_resource`, migrate to the new `AirbyteWorkspace`:

**Old (deprecated):**

```python
from dagster_airbyte import AirbyteResource, load_assets_from_airbyte_instance

airbyte_resource = AirbyteResource(host="localhost", port="8000")
assets = load_assets_from_airbyte_instance(airbyte_resource)
```

**New (recommended):**

```python
from dagster_airbyte import AirbyteWorkspace, build_airbyte_assets_definitions

airbyte_workspace = AirbyteWorkspace(
    rest_api_base_url="http://localhost:8000/api/public/v1",
    configuration_api_base_url="http://localhost:8000/api/v1",
    workspace_id="your-workspace-id"
)
assets = build_airbyte_assets_definitions(workspace=airbyte_workspace)
```

## About Airbyte

**Airbyte** is an open source data integration engine that helps you consolidate your SaaS application and database data into your data warehouses, lakes and databases.
