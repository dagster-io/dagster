---
title: 'Connections'
description: 'Automatically discover and sync data warehouse assets and metadata into Dagster'
tags: [dagster-plus-feature]
canonicalUrl: '/guides/labs/connections'
slug: '/guides/labs/connections'
sidebar_position: 30
---

import EarlyAccess from '@site/docs/partials/\_EarlyAccess.md';

<EarlyAccess />

**Connections** allow you to easily discover and sync data warehouse assets from sources like Snowflake, BigQuery, Postgres, and Databricks into Dagster. These assets are viewable in the Dagster UI catalog, and you can set alerts on schema changes or metadata values (like row count).

## Supported data warehouses

Connections currently supports the following data warehouse types, which each have their own configuration guide:

- [Snowflake](connections/snowflake)
- [BigQuery](connections/bigquery)
- [Postgres](connections/postgres)
- [Databricks](connections/databricks)

## Monitoring Connections assets with alerts

You can use alerts to monitor two kinds of changes to your Connections assets: schema changes, or metadata changes.

1. Navigate to **Deployment** > **Alerts** and click **Create alert policy**.
2. Select **Asset** as the alert type.
3. Set the target to a "Custom Selection" with `group: NAME_OF_YOUR_CONNECTION`.
4. Then select **Table schema changes** or **Metrics** as the event type, and complete the rest of the configuration.

## About the asset definitions created from Connections

The assets created by a Connection are independent from existing Dagster definitions, and use the name of your Connection as both the group name and code location name.

Connection assets emit freshness and data version information as the underlying warehouse tables change, so they can be used as dependencies to trigger downstream materializations.

Currently, metadata on assets from Connections does not impact code-defined assets, even if they point to the same underlying data warehouse table.

:::note Coming soon

Dagster is expanding what Connection assets can do across Snowflake, BigQuery, Postgres, and Databricks:

- **Linking to code-defined assets** — emitted metadata on Connection assets will be linked to matching code-defined assets that point to the same underlying warehouse table.

:::
