---
title: 'Postgres Connection'
description: 'Connect Dagster to PostgreSQL to automatically sync asset metadata'
tags: [dagster-plus-feature]
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

This guide covers connecting Dagster+ to PostgreSQL to automatically discover and sync database, schema, table, and view metadata.

## Overview

To create a PostgreSQL Connection in Dagster+, you will need to:

1. Create a PostgreSQL user with appropriate permissions
2. Add the PostgreSQL user credentials in Dagster+.
3. Create the PostgreSQL Connection in Dagster+.

## Step 1: Create a Postgres user for Dagster connections

Dagster Connections requires read-only access to PostgreSQL metadata. We recommend creating a dedicated user for this access.

Connect to your PostgreSQL database and run these commands:

```sql
-- Create a dedicated user for Dagster
CREATE USER dagster_connection WITH PASSWORD 'your-secure-password';

-- Grant connection permission
GRANT CONNECT ON DATABASE your_database TO dagster_connection;

-- Connect to the target database
\c your_database

-- Grant schema access
-- Repeat for each schema you want to sync
GRANT USAGE ON SCHEMA public TO dagster_connection;
GRANT USAGE ON SCHEMA your_schema TO dagster_connection;

-- Grant read access to tables and views
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dagster_connection;
GRANT SELECT ON ALL TABLES IN SCHEMA your_schema TO dagster_connection;

-- Grant access to future tables (recommended)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO dagster_connection;
ALTER DEFAULT PRIVILEGES IN SCHEMA your_schema
    GRANT SELECT ON TABLES TO dagster_connection;

-- Grant access to sequences (for serial columns)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO dagster_connection;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA your_schema TO dagster_connection;
```

:::info Why these permissions?

- **`CONNECT`** allows the user to connect to the database
- **`USAGE`** on schemas allows listing objects within them
- **`SELECT`** on tables is required for metadata extraction and profiling
- **`ALTER DEFAULT PRIVILEGES`** ensures new tables are automatically accessible

:::

## Step 2: Store the PostgreSQL user password in Dagster+

1. In Dagster+, navigate to **Deployment** > **Environment variables**

2. Create a new environment variable:
   - **Name**: `POSTGRES_CONNECTION_PASSWORD` (or any name you prefer)
   - **Value**: Your PostgreSQL password

:::warning Security

Never hardcode database passwords in configuration files or commit them to version control. Always use environment variables.

:::

## Step 3: Create the Postgres Connection

1. In Dagster+, click **Connections** in the left sidebar
2. Click **Create Connection**
3. Select **Postgres** as the connection type
4. Configure the connection details

### Required fields

- **Connection name**: A unique name for this Connection (e.g., `postgres_production`)
  - This will become the name of the code location containing synced assets
- **Hostname**: Database server hostname (e.g., `db.example.com` or `10.0.1.50`)
- **Port**: Database port (defaults to `5432`)
- **Username**: PostgreSQL username (e.g., `dagster_connection`)
- **Password environment variable**: Name of the Dagster+ environment variable containing your password (e.g., `POSTGRES_CONNECTION_PASSWORD`)

### Optional: Configure asset filtering

Use filtering to control which databases, schemas, tables, and views are synced. Patterns use regular expressions.
