---
title: 'Databricks Connection'
description: 'Connect Dagster to Databricks to automatically sync asset metadata'
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

This guide covers connecting Dagster+ to Databricks Unity Catalog to automatically discover and sync catalog, schema, table, and view metadata.

## Overview

To create a Databricks Connection in Dagster+, you will need to:

1. Generate an authentication token with appropriate permissions.
2. Add the authentication token as an environment variable in Dagster+.
3. Create the Databricks Connection in Dagster+.

## Step 1: Generate an authentication token with appropriate permissions

Dagster Connections require read-only access to Databricks Unity Catalog metadata. We recommend using a dedicated service principal,
but personal access tokens (PATs) are also supported.

### Option A: Create a Service principal (recommended for production)

Service principals provide more secure, auditable access without tying to a specific user account.

#### Step 1A.1: Create service principal

1. In your Databricks workspace, navigate to **Settings** > **Admin Console**.
2. Click **Service principals** in the left sidebar.
3. Click **Add service principal**.
4. Enter a name like `dagster-connection`.
5. Click **Add**.

#### Step 1A.2: Grant Unity Catalog permissions

Grant these privileges on the catalogs and schemas you want to sync:

```sql
-- Grant catalog access
GRANT USE CATALOG ON CATALOG <catalog_name> TO `dagster-connection`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA <catalog_name>.<schema_name> TO `dagster-connection`;

-- Grant read access to tables and views
GRANT SELECT ON SCHEMA <catalog_name>.<schema_name> TO `dagster-connection`;
```

#### Step 1A.3: Generate access token for service principal

1. In the Admin Console, find your `dagster-connection` service principal
2. Click the **Generate token** button
3. Set an expiration period (or "no expiration" for long-term use)
4. Copy the generated token - it will only be shown once

### Option B: Personal access token

For simpler setups or development environments, you can use a PAT tied to your user account.

#### Step 1B.1: Ensure your user has required permissions

Your user account needs these Unity Catalog privileges:

- `USE CATALOG` on target catalogs
- `USE SCHEMA` on target schemas
- `SELECT` on tables and views

#### Step 1B.2: Create personal access token

1. Click your username in the top-right corner of the Databricks workspace
2. Select **User Settings**
3. Navigate to the **Developer** tab
4. Click **Manage** next to **Access tokens**
5. Click **Generate new token**
6. Enter a comment like "Dagster Connection"
7. Set expiration (or leave blank for no expiration)
8. Click **Generate**
9. Copy the token immediately - it won't be shown again

## Step 2: Store access token in Dagster+

1. In Dagster+, navigate to **Deployment** > **Environment variables**

2. Create a new environment variable:
   - **Name**: `DATABRICKS_CONNECTION_TOKEN` (or any name you prefer)
   - **Value**: Paste your service principal token or PAT

## Step 3: Create the Databricks Connection

1. In Dagster+, click **Connections** in the left sidebar
2. Click **Create Connection**
3. Select **Databricks** as the connection type
4. Configure the connection details

### Required fields

- **Connection name**: A unique name for this Connection (e.g., `databricks_unity_catalog`)
  - This will become the name of the code location containing synced assets
- **Workspace URL**: Your Databricks workspace URL
  - Format: `https://dbc-1234abcd-56ef.cloud.databricks.com`
  - Find this in your browser address bar when logged into Databricks
- **Personal access token environment variable**: Name of the Dagster+ environment variable containing your token (e.g., `DATABRICKS_CONNECTION_TOKEN`)

### Optional: Configure asset filtering

Use filtering to control which catalogs, schemas, tables, views, and notebooks are synced. Patterns use regular expressions.
