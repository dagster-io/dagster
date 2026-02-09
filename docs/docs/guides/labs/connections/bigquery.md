---
title: 'BigQuery Connection'
description: 'Connect Dagster to BigQuery to automatically sync asset metadata'
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

This guide covers connecting Dagster+ to Google BigQuery to automatically discover and sync dataset, table, and view metadata.

## Overview

To create a BigQuery Connection in Dagster+, you will need to:

1. Create a GCP service account.
2. Set up authentication in Dagster+.
3. Create the BigQuery Connection in Dagster+.

## Step 1: Create a GCP service account and grant permissions

Dagster requires read-only access to BigQuery metadata. We recommend creating a dedicated GCP service account for Dagster Connections.

### Step 1.1: Create a GCP service account

1. Open the [GCP Console](https://console.cloud.google.com).
2. Navigate to **IAM & Admin** > **Service Accounts**.
3. Click **Create Service Account**.
4. Enter a name for the account, such as `dagster-connection`.
5. Click **Create and Continue**.

### Step 1.2: Grant required permissions

The service account needs two sets of permissions: permissions on target projects (projects with data to sync) and permissions on the extractor project (where the service account resides).

#### Step 1.2.1: Grant permissions on target projects (projects with data to sync)

Grant the **BigQuery Metadata Viewer** role, which includes:

- `bigquery.datasets.get` - Read dataset metadata
- `bigquery.datasets.getIamPolicy` - Access dataset permissions
- `bigquery.tables.list` - List tables in datasets
- `bigquery.tables.get` - Read table metadata
- `bigquery.routines.get` and `bigquery.routines.list` - Access stored procedures

To grant this role:

1. Navigate to **IAM & Admin** > **IAM** in the GCP Console
2. Click **Grant Access**
3. Enter your service account email
4. Select role: **BigQuery Metadata Viewer** (`roles/bigquery.metadataViewer`)
5. Click **Save**

Repeat this for each project containing data you want to sync.

#### Step 1.2.2: Grant permissions on the extractor project (where the service account resides)

The service account needs to execute queries for metadata extraction. Grant the **BigQuery Job User** role, which includes:

- `bigquery.jobs.create` - Execute metadata queries
- `bigquery.jobs.list` - List job status
- `bigquery.readsessions.create` - Create read sessions for large results
- `bigquery.readsessions.getData` - Read session data

To grant this role:

1. In the project where your service account was created, navigate to **IAM**.
2. Find your service account.
3. Add role: **BigQuery Job User** (`roles/bigquery.jobUser`).

### Step 1.3: (Optional) Enable lineage and usage tracking

To track table lineage and usage statistics, add:

- `bigquery.jobs.listAll` - View all jobs for lineage extraction
- `logging.logEntries.list` - Access audit logs for usage tracking

These are available in the **BigQuery Resource Viewer** role (`roles/bigquery.resourceViewer`).

### Step 1.4: Enable required APIs

Ensure these APIs are enabled in your GCP project:

```bash
gcloud services enable bigquery.googleapis.com
gcloud services enable bigquerystorage.googleapis.com
```

Or enable them in the [GCP Console](https://console.cloud.google.com/apis/library).

## Step 2: Set up authentication in Dagster+

### Step 2.1: Create and download service account key from GCP

1. In **IAM & Admin** > **Service Accounts**, find your `dagster-connection` service account
2. Click the service account email to open details
3. Navigate to the **Keys** tab
4. Click **Add Key** > **Create new key**
5. Choose **JSON** format
6. Click **Create** - the key file will download automatically

:::warning Service account key security

Service account keys provide full access to your GCP resources. Store them securely and never commit them to version control.

:::

### Step 2.2: Encode credentials and store them in Dagster+

BigQuery credentials must be base64-encoded before storing in Dagster+:

1. Encode your JSON key file:

```bash
base64 -i /path/to/your-key-file.json
```

Or on Linux:

```bash
base64 -w 0 /path/to/your-key-file.json
```

2. Copy the base64-encoded output

3. In Dagster+, navigate to **Deployment** > **Environment variables**

4. Create a new environment variable:
   - **Name**: `BIGQUERY_CONNECTION_CREDENTIALS` (or any name you prefer)
   - **Value**: Paste the base64-encoded string

## Step 3: Create the BigQuery connection in Dagster+

1. In Dagster+, click **Connections** in the left sidebar
2. Click **Create Connection**
3. Select **BigQuery** as the connection type
4. Configure the connection details

### Required fields

- **Connection name**: A unique name for this Connection (e.g., `bigquery_analytics`)
  - This will become the name of the code location containing synced assets
- **Google application credentials environment variable**: Name of the Dagster+ environment variable containing your base64-encoded service account JSON (e.g., `BIGQUERY_CONNECTION_CREDENTIALS`)

### Optional: Configure region qualifiers

Specify which BigQuery regions to scan. Defaults to `region-us` and `region-eu` if not specified:

```json
{
  "region_qualifiers": ["region-us", "region-eu", "region-asia-northeast1"]
}
```

Region qualifiers help optimize scanning for multi-region datasets.

### Optional: Configure asset filtering

Use filtering to control which projects, datasets, tables, and views are synced. Patterns use regular expressions.
