---
title: Data ingestion with Sling
description: Ingest CSV files into DuckDB using Sling replication
sidebar_position: 10
---

The first step in our pipeline is data ingestion. We'll use [Sling](https://slingdata.io/), a data replication tool that can move data between various sources and targets. In this case, we'll load CSV files from the local filesystem into DuckDB tables.

## Understanding the data

Our pipeline works with three CSV files containing e-commerce data:

- `raw_customers.csv`: Customer information (ID, first name, last name)
- `raw_orders.csv`: Order details (ID, user ID, order date, status)
- `raw_payments.csv`: Payment information (ID, order ID, payment method, amount)

These files represent a typical e-commerce dataset that you might need to analyze for business insights.

## Sling replication component

Dagster includes a built-in [Sling component](/integrations/libraries/sling) that handles data replication tasks. This component reads a YAML configuration file that defines how data should be moved from source to target systems.

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/defs/ingest_files/component.yaml"
  language="yaml"
  startAfter="start_sling_component_config"
  endBefore="end_sling_component_config"
  title="src/sql_but_not_dbt/defs/ingest_files/component.yaml"
/>

The component configuration specifies:

- **Type**: Uses the `SlingReplicationCollectionComponent` from `dagster_components.dagster_sling`
- **Replications**: Points to the `replication.yaml` file that contains the actual replication logic
- **Asset attributes**: Commented out group name that could be used to organize assets

## Replication configuration

The core replication logic is defined in a separate YAML file that Sling understands:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/defs/ingest_files/replication.yaml"
  language="yaml"
  startAfter="start_sling_replication_config"
  endBefore="end_sling_replication_config"
  title="src/sql_but_not_dbt/defs/ingest_files/replication.yaml"
/>

This configuration defines:

- **Source**: `LOCAL` filesystem where the CSV files are located
- **Target**: `DUCKDB` database where data will be loaded
- **Defaults**: Applied to all streams (full-refresh mode, table naming pattern)
- **Streams**: Individual file mappings from source files to target tables

## How the ingestion works

When this component runs, it:

1. **Reads CSV files**: Sling reads each CSV file from the local filesystem
2. **Creates DuckDB tables**: For each file, it creates a corresponding table in DuckDB
3. **Loads data**: Uses full-refresh mode to completely replace table contents
4. **Tracks lineage**: Dagster automatically creates assets for each table, enabling lineage tracking

The `full-refresh` mode means that each time the pipeline runs, it completely replaces the target tables with fresh data from the CSV files. This is appropriate for small datasets or when you always want the latest complete snapshot.

## Component discovery

Dagster automatically discovers this component because it's located in the `defs/` directory structure. The main `definitions.py` file uses the `build_component_defs` function to scan for components:

<CodeExample
  path="docs_projects/project_sql_but_not_dbt/src/sql_but_not_dbt/definitions.py"
  language="python"
  startAfter="start_build_component_defs"
  endBefore="end_build_component_defs"
  title="src/sql_but_not_dbt/definitions.py"
/>

This approach allows you to organize your pipeline into logical components without having to manually register each one in your Python code.

## Asset creation

When the Sling component runs, it automatically creates Dagster assets for each target table. These assets will appear in the Dagster UI with:

- Asset keys matching the table names (`main/raw_customers`, `main/raw_orders`, `main/raw_payments`)
- Metadata about the replication process
- Lineage information showing the relationship to downstream transformations

The assets created by this component serve as the foundation for downstream SQL transformations, creating a clear data lineage from raw files to processed analytics.

## Next steps

Now that we understand how data ingestion works, let's explore how to [create custom SQL components](/examples/full-pipelines/sql-but-not-dbt/custom-sql-component) for data transformations.
