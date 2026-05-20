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

1. Generate authentication credentials with appropriate permissions.
2. Add the credentials as an environment variable in Dagster+.
3. Create the Databricks Connection in Dagster+.

## Step 1: Generate authentication credentials with appropriate permissions

Dagster Connections require read-only access to Databricks Unity Catalog metadata. We recommend using a dedicated service principal with OAuth machine-to-machine (M2M) credentials, but personal access tokens (PATs) are also supported.

### Required API scopes

The Databricks credentials used by the connection must be able to access the following [API scopes](https://docs.databricks.com/api/workspace/api/scopes):

- **`unity-catalog`** — Read catalog, schema, table, and view metadata from Unity Catalog, and data lineage between Unity Catalog objects.
- **`query-history`** — Read query history to surface usage information and derive table-level lineage.
- **`sql`** — Execute lineage queries against a SQL warehouse. Only required if you [enable lineage tracking](#optional-enable-lineage-tracking).

When creating a personal access token, select these scopes explicitly. Service principal OAuth credentials inherit scopes from the principal's permissions.

### Option A: Service principal with OAuth (M2M) — recommended for production

Service principals provide more secure, auditable access without tying to a specific user account. Dagster authenticates to the service principal using OAuth machine-to-machine (M2M) credentials — a client ID and a client secret.

#### Step 1A.1: Create service principal

1. In your Databricks workspace, navigate to **Settings** > **Admin Console**.
2. Click **Service principals** in the left sidebar.
3. Click **Add service principal**.
4. Enter a name like `dagster-connection`.
5. Click **Add**.
6. Open the new service principal's details page and copy its **Application ID** (a UUID). You'll use this value both for Unity Catalog grants and for the connection's Client ID.

#### Step 1A.2: Grant Unity Catalog permissions

In Unity Catalog, grants to a service principal must use its **Application ID**, not its display name. Run the following against each catalog and schema you want to sync, replacing `<application_id>` with the UUID from the previous step:

```sql
-- Grant catalog access
GRANT USE CATALOG ON CATALOG <catalog_name> TO `<application_id>`;

-- Grant schema access
GRANT USE SCHEMA ON SCHEMA <catalog_name>.<schema_name> TO `<application_id>`;

-- Grant read access to tables and views
GRANT SELECT ON SCHEMA <catalog_name>.<schema_name> TO `<application_id>`;
```

#### Step 1A.3: Generate an OAuth secret for the service principal

1. In the Admin Console, open your `dagster-connection` service principal.
2. Navigate to the **Secrets** tab.
3. Click **Generate secret**.
4. Set a lifetime (or "no expiration" for long-term use).
5. Copy the **Secret** — it will only be shown once. Combined with the Application ID from Step 1A.1, this gives you the Client ID and Client Secret used by the connection.

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

### Optional: Enable lineage tracking

To compute table lineage from Databricks query history, additional configuration is required regardless of which authentication option you chose:

- The service principal or user tied to the credentials used for the connection must have access to the metastore system tables. This typically requires one of:
  - **Metastore admin** privileges, or
  - **Account admin** privileges, which are required when the metastore was created by default at account creation time
- The **warehouse ID** of a SQL warehouse that the above identity can access must be provided when configuring the connection (see [Step 3](#step-3-create-the-databricks-connection)). Lineage queries are executed against this warehouse.

## Step 2: Store credentials in Dagster+

1. In Dagster+, navigate to **Deployment** > **Environment variables**

2. Create a new environment variable to hold your credential:

   - If you used **Option A** (service principal with M2M OAuth):
     - **Name:** `DATABRICKS_CONNECTION_CLIENT_SECRET` (or any name you prefer)
     - **Value:** Paste your OAuth secret
   - If you used **Option B** (PAT):
     - **Name:** `DATABRICKS_CONNECTION_TOKEN` (or any name you prefer)
     - **Value:** Paste your PAT

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
- **Authentication**: Fill in the fields that match the method you chose in [Step 1](#step-1-generate-authentication-credentials-with-appropriate-permissions):
  - If you used **Option A** (service principal with M2M OAuth):
    - **Client ID:** The service principal's Application ID
    - **Client secret environment variable:** Name of the Dagster+ environment variable containing your OAuth secret (e.g., `DATABRICKS_CONNECTION_CLIENT_SECRET`)
  - If you used **Option B** (PAT):
    - **Personal access token environment variable:** Name of the Dagster+ environment variable containing your PAT (e.g., `DATABRICKS_CONNECTION_TOKEN`)

### Optional: Warehouse ID for lineage tracking

- **Warehouse ID**: ID of the SQL warehouse used to execute lineage queries against the metastore system tables. Required to enable lineage tracking. For the permissions the connection identity must have, see [Enable lineage tracking](#optional-enable-lineage-tracking).

### Optional: Configure asset filtering

Use filtering to control which catalogs, schemas, tables, views, and notebooks are synced. Patterns use regular expressions.

## Connection freshness

When the Databricks Connection has a SQL warehouse configured, Dagster automatically tracks changes to your Unity Catalog tables and emits a materialization on the corresponding Connection asset each time the underlying table is updated in Databricks. As a result, your Connection assets reflect the most recent state of the Databricks tables without needing to define a sensor or schedule.

### Prerequisites

Connection freshness for Databricks shares the same configuration as lineage tracking:

- A **Warehouse ID** is set on the Connection ([Warehouse ID for lineage tracking](#optional-warehouse-id-for-lineage-tracking)).
- The connection identity has access to the Unity Catalog metastore ([Enable lineage tracking](#optional-enable-lineage-tracking)).

If no warehouse is configured, freshness signals are not emitted.

### Triggering downstream assets

Each detected change produces a standard Dagster materialization event on the Connection asset, so code-defined assets can depend on a Connection asset like any other upstream. Combine that with an [Automation Condition](/guides/automate/declarative-automation) to materialize a downstream asset whenever its Databricks parent changes:

<CodeExample
  path="docs_snippets/docs_snippets/guides/labs/connections/databricks/connection_freshness_downstream.py"
  language="python"
  title="src/<project_name>/defs/assets.py"
/>
