---
title: 'Snowflake Connection'
description: 'Connect Dagster to Snowflake to automatically sync asset metadata'
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

This guide covers connecting Dagster+ to Snowflake to automatically discover and sync table and view metadata.

## Overview

To create a Snowflake Connection in Dagster+, you will need to:

1. Create a Snowflake role and user with appropriate permissions
2. Add the Snowflake credentials in Dagster+.
3. Create the Snowflake Connection in Dagster+.

## Step 1: Create Snowflake role and user with appropriate permissions

### Step 1.1: Create role and user to use with Dagster Connections

Dagster requires read-only access to Snowflake metadata. We recommend creating a dedicated role and user for Dagster Connections.

Run the following SQL commands in Snowflake to create a role with minimum required permissions:

```sql
-- Create a dedicated role for Dagster
CREATE OR REPLACE ROLE dagster_connection_role;

-- Grant warehouse access (required to run metadata queries)
GRANT OPERATE, USAGE ON WAREHOUSE "<your-warehouse>" TO ROLE dagster_connection_role;

-- Grant database and schema access
-- Repeat for each database you want to sync
GRANT USAGE ON DATABASE "<your-database>" TO ROLE dagster_connection_role;
GRANT USAGE ON ALL SCHEMAS IN DATABASE "<your-database>" TO ROLE dagster_connection_role;
GRANT USAGE ON FUTURE SCHEMAS IN DATABASE "<your-database>" TO ROLE dagster_connection_role;

-- Grant table and view access for metadata discovery
GRANT REFERENCES ON ALL TABLES IN DATABASE "<your-database>" TO ROLE dagster_connection_role;
GRANT REFERENCES ON FUTURE TABLES IN DATABASE "<your-database>" TO ROLE dagster_connection_role;
GRANT REFERENCES ON ALL VIEWS IN DATABASE "<your-database>" TO ROLE dagster_connection_role;
GRANT REFERENCES ON FUTURE VIEWS IN DATABASE "<your-database>" TO ROLE dagster_connection_role;

-- Create user for Dagster
CREATE USER dagster_connection_user
  DEFAULT_ROLE = dagster_connection_role
  MUST_CHANGE_PASSWORD = FALSE;

-- Assign role to user
GRANT ROLE dagster_connection_role TO USER dagster_connection_user;
```

:::info Why these permissions?

- **`USAGE`** on database/schema allows Dagster to list and access objects within them
- **`REFERENCES`** is the minimum privilege for metadata discovery without accessing actual data
- **`OPERATE` and `USAGE`** on warehouse allow Dagster to run metadata queries
- Grants on `FUTURE` objects ensure new tables/views are automatically discoverable

:::

### Step 1.2: (Optional) Grant lineage tracking permissions

To track table lineage from Snowflake query history, grant access to system tables:

```sql
-- Grant access to Snowflake system tables for lineage
GRANT IMPORTED PRIVILEGES ON DATABASE snowflake TO ROLE dagster_connection_role;
```

:::note

This permission provides access to Snowflake's `ACCOUNT_USAGE` views, which contain query history used for lineage extraction.
This requires Snowflake Enterprise Edition or higher.

:::

## Step 2: Add your Snowflake user credentials to Dagster+

Dagster supports RSA key pair authentication for Snowflake Connections.

### Step 2.1: Create a key pair for your Snowflake user

Generate a key pair and assign it to your Snowflake user (see https://docs.snowflake.com/en/user-guide/key-pair-auth)

### Step 2.2: Store the private key as an environment variable in Dagster+

1. Copy the entire content of your Snowflake private key, including the `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----` lines

2. In Dagster+, navigate to **Deployment** > **Environment variables**

3. Create a new environment variable:
   - **Name**: `SNOWFLAKE_CONNECTION_PRIVATE_KEY` (or any name you prefer)
   - **Value**: Paste the entire private key content

:::warning Security

Never commit private keys to version control. Always store them as environment variables or in a secure secret manager.

:::

## Step 3: Create the Snowflake Connection

1. In Dagster+, click **Connections** in the left sidebar.
2. Click **Create Connection**.
3. Select **Snowflake** as the connection type.
4. Configure the connection details.

### Required fields

- **Connection name**: A unique name for this Connection (e.g., `snowflake_analytics`)
  - This will become the name of the code location containing synced assets
- **Account ID**: Your Snowflake account identifier
  - Format: `xy12345.us-east-1` or `xy12345.us-east-1.aws`
  - Find this in your Snowflake URL: `https://<account_id>.snowflakecomputing.com`
- **Warehouse**: The Snowflake warehouse to use for metadata queries
- **Username**: The Snowflake username (e.g., `dagster_connection_user`)
- **Role**: The Snowflake role name (e.g., `dagster_connection_role`)
- **Private key environment variable**: Name of the Dagster+ environment variable containing your private key (e.g., `SNOWFLAKE_CONNECTION_PRIVATE_KEY`)

### Optional: Configure asset filtering

Use filtering to control which databases, schemas, and tables are synced. Patterns use regular expressions.
