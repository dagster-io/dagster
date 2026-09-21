---
title: Ingest data with Sling
description: Use the SlingReplicationCollectionComponent to ingest Postgres tables into DuckDB
sidebar_position: 10
---

[Sling](https://slingdata.io/) is a data movement tool that replicates tables between databases, data warehouses, and file systems. In this step, you'll configure Sling to copy tables from Postgres to DuckDB and register each table as a Dagster asset.

## Step 1: Scaffold the Sling component

Use `dg scaffold` to create the component folder:

```shell
dg scaffold defs dagster_sling.SlingReplicationCollectionComponent sling_ingest
```

This creates a `sling_ingest` folder with two files:

```
src/project_elt_pipeline/defs/
└── sling_ingest/
    ├── defs.yaml
    └── replication.yaml
```

`defs.yaml` already has the necessary configuration and is ready to use:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/sling_ingest/defs.yaml"
  language="yaml"
  title="src/project_elt_pipeline/defs/sling_ingest/defs.yaml"
/>

`replication.yaml` is where you define what to replicate and where to send it, which we cover in the next step.

## Step 2: Configure the replication

### Step 2.1: Update replication.yaml

Replace the contents of `defs/sling_ingest/replication.yaml` with your Postgres-to-DuckDB config:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/sling_ingest/replication.yaml"
  language="yaml"
  title="src/project_elt_pipeline/defs/sling_ingest/replication.yaml"
/>

:::note

A few things to note:

- `POSTGRES_SOURCE` and `DUCKDB_TARGET` are the connection names used in `source:` and `target:` at the top. Sling reads their definitions from the `env:` block.
- `mode: incremental` tracks changes since the last run using `update_key`, while `full-refresh` replaces the table on every run.
- The `object:` field sets the destination table name.

:::

### Step 2.2: Set connection details

Set the connection details in a `.env` file at your project root:

```shell title=".env"
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=mydb
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
DEST_DUCKDB_PATH=./data.duckdb
```

## Step 3: Verify the component

Run `dg check defs` to confirm the component loads without errors:

```shell
dg check defs
```

## Step 4: View assets in Dagster

Reload definitions in the Dagster UI (**Deployment** > **Reload definitions**). You should see three new assets grouped under `sling_ingest`: `users`, `orders`, and `products`. Each asset corresponds to one stream in `replication.yaml`.

With a running Postgres instance and your `.env` file in place, click **Materialize all** to run the replication.

## How assets are generated

`SlingReplicationCollectionComponent` reads `replication.yaml` and creates one Dagster asset per stream — no `@asset` functions required. Add a stream to `replication.yaml` and a new asset appears in the graph. Remove one and it disappears.

## Next steps

- Continue this example by [adding dlt ingestion](/examples/full-pipelines/elt-pipeline/dlt-ingest)
