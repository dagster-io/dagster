---
title: Ingest data with dlt
description: Use the DltLoadCollectionComponent to ingest GitHub API data into DuckDB
sidebar_position: 20
---

[dlt](https://dlthub.com/) (data load tool) is a Python library for loading data from APIs and other sources into a destination. It handles schema inference, type coercion, and write modes (merge, append, replace) automatically. In this step, you'll use dlt to load GitHub issues and pull requests into DuckDB and register them as Dagster assets.

## Step 1: Scaffold the dlt component definition

Use `dg scaffold` to create the component folder:

```shell
dg scaffold defs dagster_dlt.DltLoadCollectionComponent dlt_ingest
```

This creates a `dlt_ingest` folder with two files:

```
src/project_elt_pipeline/defs/
└── dlt_ingest/
    ├── defs.yaml
    └── loads.py
```

`loads.py` is where you define what to load and where to send it. `defs.yaml` references those definitions for the component.

## Step 2: Define the dlt resources and pipeline

Replace the contents of `defs/dlt_ingest/loads.py`:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/dlt_ingest/loads.py"
  language="python"
  title="src/project_elt_pipeline/defs/dlt_ingest/loads.py"
/>

Here's what each part does:

- **`@dlt.resource`** marks a function as a dlt resource — each resource maps to one table in the destination database. `write_disposition="merge"` upserts rows by `primary_key` so re-running doesn't create duplicates.
- **`@dlt.source`** groups resources together. Returning `issues` and `pull_requests` (without calling them) tells dlt to include both.
- **`github_pipeline`** defines the destination (DuckDB in this case) with a dataset (schema) named `github_data`.
- **`github_load_source`** is the instantiated source object that is referenced by the component.

Set your repo and token in `.env`:

```shell title=".env"
GITHUB_TOKEN=your_token_here
GITHUB_REPO=dagster-io/dagster
```

:::tip

A GitHub token isn't required for public repos, but without one you'll hit GitHub's low unauthenticated rate limit (60 requests/hour) quickly.

:::

## Step 3: Configure the component definition

Update `defs/dlt_ingest/defs.yaml` to reference your pipeline and source:

<CodeExample
  path="docs_projects/project_elt_pipeline/src/project_elt_pipeline/defs/dlt_ingest/defs.yaml"
  language="yaml"
  title="src/project_elt_pipeline/defs/dlt_ingest/defs.yaml"
/>

The `.loads.` prefix is a relative module reference — `loads` refers to `loads.py` in the same directory, and `github_load_source` / `github_pipeline` are the module-level objects defined there.

`DltLoadCollectionComponent` inspects the source and creates one Dagster asset per dlt resource — in this case, `issues` and `pull_requests`, both in the `github` asset group.

## Step 4: Verify the component

Run `dg check defs` to confirm the component loads without errors:

```shell
dg check defs
```

## Step 5: View assets in Dagster

Reload definitions in the Dagster UI. You should now see assets from both components:

- **sling_ingest** group: `users`, `orders`, `products` (replicated from Postgres)
- **github** group: `issues`, `pull_requests` (loaded from the GitHub API)

With `GITHUB_TOKEN` set in `.env`, click **Materialize all** on the github assets to load data into DuckDB.

## How assets are generated

`DltLoadCollectionComponent` inspects the dlt source and creates one Dagster asset per resource — no `@asset` functions required. In this case, the `issues` and `pull_requests` resources each become an asset in the `github` group. Add a resource to your source and a new asset appears. Remove one and it disappears.

## Summary

You now have two ingestion pipelines running as Dagster assets:

- **Sling** handles database-to-database replication — configure a stream in YAML and it appears as an asset
- **dlt** handles API ingestion with automatic schema inference — define a resource in Python and it becomes an asset

Raw data is in DuckDB, but the pipeline isn't complete yet. The next step adds the **T** — SQL transformation components that produce analytics-ready outputs using the same component-forward approach.

:::note

The transforms in the next step use the Postgres tables (`users`, `orders`, `products`) loaded by Sling. The `issues` and `pull_requests` assets are available in your asset graph as a starting point for additional transforms — for example, aggregating issue counts by label or tracking PR cycle times.

:::

## Next steps

- Continue this example by [adding SQL transformations](/examples/full-pipelines/elt-pipeline/transform)
