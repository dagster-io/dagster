---
title: Transform data with SQL
description: Use TemplatedSqlComponent to write SQL transforms that depend on ingested data
sidebar_position: 30
---

You now have raw data being written to DuckDB tables from two sources: Postgres tables replicated by Sling, and GitHub data loaded by dlt. This step adds the "Transform" in ELT: SQL transformations that turn raw ingested tables into analytics-ready outputs.

To transform the data, you'll use the `TemplatedSqlComponent` rather than an `@asset`-decorated function. Each transform becomes a component folder with a `defs.yaml` and a `.sql` file, keeping SQL out of Python and giving you full lineage in the asset graph.

## Step 1: Create a DuckDB connection component

`TemplatedSqlComponent` executes SQL through a connection object. DuckDB doesn't ship a built-in connection component, so you'll write a small one in your project's `components/` folder.

Add the `DuckDBConnectionComponent` class to `duckdb_connection.py`:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/components/duckdb_connection.py"
  language="python"
  title="src/project_elt_pipeline/components/duckdb_connection.py"
/>

## Step 2: Scaffold the DuckDB connection component definition

Scaffold a component folder to hold the DuckDB connection config:

```shell
dg scaffold defs project_elt_pipeline.DuckDBConnectionComponent duckdb_connection
```

This creates:

```
src/project_elt_pipeline/defs/duckdb_connection/
└── defs.yaml
```

The generated `defs.yaml` references your component type and reads the database path from your `.env` file:

```yaml title="src/project_elt_pipeline/defs/duckdb_connection/defs.yaml"
type: project_elt_pipeline.DuckDBConnectionComponent

attributes:
  database: '{{ env.DEST_DUCKDB_PATH }}'
```

We will use this connection component in multiple transform components.

## Step 3: Scaffold the transform component definitions

Scaffold one component folder per transform:

```shell
dg scaffold defs dagster.TemplatedSqlComponent customer_order_summary
dg scaffold defs dagster.TemplatedSqlComponent product_revenue
```

This creates:

```
src/project_elt_pipeline/defs/
├── customer_order_summary/
│   └── defs.yaml
└── product_revenue/
    └── defs.yaml
```

## Step 4: Write the SQL files

Create a `.sql` file in each component folder. Keeping SQL in its own file gives you syntax highlighting and keeps `defs.yaml` focused on configuration.

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/customer_order_summary/customer_order_summary.sql"
  language="sql"
  title="src/project_elt_pipeline/defs/customer_order_summary/customer_order_summary.sql"
/>

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/product_revenue/product_revenue.sql"
  language="sql"
  title="src/project_elt_pipeline/defs/product_revenue/product_revenue.sql"
/>

## Step 5: Configure the component definitions

Update each `defs.yaml` to reference the SQL file, declare upstream dependencies, and reference the DuckDB connection:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/customer_order_summary/defs.yaml"
  language="yaml"
  title="src/project_elt_pipeline/defs/customer_order_summary/defs.yaml"
/>

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/product_revenue/defs.yaml"
  language="yaml"
  title="src/project_elt_pipeline/defs/product_revenue/defs.yaml"
/>

`deps` tells Dagster which upstream assets each transform reads from — the same `users`, `orders`, and `products` assets produced by the Sling component. Dagster uses this to draw edges in the asset graph, enforce materialization order, and propagate staleness when upstream data changes.

`load_component_at_path('../duckdb_connection')` loads the connection component defined in the sibling folder.

## Step 6: Verify and view

Run `dg check defs` to confirm all assets load without errors:

```shell
dg check defs
```

Reload definitions in the Dagster UI. You should now see three asset groups:

- **sling_ingest**: `users`, `orders`, `products`
- **github**: `issues`, `pull_requests`
- **transforms**: `customer_order_summary`, `product_revenue`

Open the asset graph and expand the **sling_ingest** and **transforms** groups. You'll see edges connecting `users` to `customer_order_summary`, `orders` to both transform assets, and `products` to `product_revenue`.

To run the full pipeline, select all assets and click **Materialize all**. Dagster will sequence the run so ingestion completes before transformations start.

## How assets are generated

`TemplatedSqlComponent` creates one Dagster asset per SQL transform, using `deps` to wire upstream ingestion assets into the graph — no `@asset` functions required. Add a component folder with a `.sql` file and it joins the graph. Remove one and it disappears. Dagster uses the declared `deps` to enforce materialization order and propagate staleness when upstream data changes.

## The full project structure

```
src/project_elt_pipeline/
├── components/
│   ├── __init__.py
│   └── duckdb_connection.py
├── definitions.py
└── defs/
    ├── sling_ingest/
    │   ├── defs.yaml
    │   └── replication.yaml
    ├── dlt_ingest/
    │   ├── defs.yaml
    │   └── loads.py
    ├── duckdb_connection/
    │   └── defs.yaml
    ├── customer_order_summary/
    │   ├── defs.yaml
    │   └── customer_order_summary.sql
    └── product_revenue/
        ├── defs.yaml
        └── product_revenue.sql
```

:::note

`definitions.py` discovers everything in `defs/`, since component folders are loaded automatically without any explicit imports.

:::

## Summary

You've completed the full ELT pipeline using a consistent component-forward approach throughout:

- **Extract + Load** (Sling): Postgres tables replicated into DuckDB via `SlingReplicationCollectionComponent`
- **Extract + Load** (dlt): GitHub API data loaded via `DltLoadCollectionComponent`
- **Transform**: SQL assets declared as `TemplatedSqlComponent` with upstream `deps` for full lineage

From here you can [add a schedule](/guides/automate/schedules) to run the full asset graph on a cadence, or use [asset checks](/guides/test/asset-checks) to validate data quality after each step.
