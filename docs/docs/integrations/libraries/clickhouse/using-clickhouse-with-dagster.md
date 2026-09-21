---
title: 'Using ClickHouse with Dagster'
description: Store and load Dagster assets in ClickHouse using a resource or I/O managers.
sidebar_position: 100
---

This guide shows how to use ClickHouse with Dagster [assets](/guides/build/assets/defining-assets). The `dagster-clickhouse` library provides:

- [Resource](/guides/build/external-resources): Run SQL directly inside an asset using <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseResource" /> and a [`clickhouse_driver.Client`](https://clickhouse-driver.readthedocs.io/en/latest/quickstart.html#selecting-data).
- [I/O manager](/guides/build/io-managers): Let Dagster materialize and load **Pandas** or **Polars** DataFrames as ClickHouse tables using <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_pandas" object="ClickhousePandasIOManager" /> or <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_polars" object="ClickhousePolarsIOManager" />.

You can use either approach, or both, depending on whether you want full control over SQL or you prefer Dagster to manage table storage and loads.

:::tip

Dagster’s **`schema`** (on assets and I/O managers) maps to a **ClickHouse database name**. The connection’s `database` setting is the default database **on the server session**, which is separate from the database used in fully qualified table names for assets.

:::

## Prerequisites

- **Install** the libraries you need:

  <PackageInstallInstructions packageName="dagster-clickhouse dagster-clickhouse-pandas" />

  For Polars, add `dagster-clickhouse-polars` to the list.

- **A ClickHouse instance** reachable from your Dagster code (for example `localhost:9000` for the native protocol).

## Option 1: Using the ClickHouse resource

### Step 1: Configure the resource

Add <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseResource" /> to your `Definitions`. You must set **`host`**; **`port`** defaults to **9000** (native protocol).

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/resource/configuration.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Step 2: Create tables with SQL

Use `get_connection()` to obtain a `clickhouse_driver.Client`. The following asset downloads the Iris sample CSV and loads it into the `iris.iris_dataset` table:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/resource/create_table.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Step 3: Downstream assets

You can run arbitrary SQL (for example `CREATE TABLE … AS SELECT`) in a downstream asset that depends on `iris_dataset`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/resource/downstream.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Completed example (resource)

<CodeExample path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/resource/full_example.py" />

## Option 2: Using the ClickHouse I/O manager (Pandas)

### Step 1: Configure the I/O manager

Configure <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_pandas" object="ClickhousePandasIOManager" /> with connection fields and an optional default **`schema`** (ClickHouse database) for table assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/io_manager/configuration.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Step 2: Materialize a DataFrame as a table

Return a **Pandas** DataFrame from an asset. Dagster creates a **MergeTree** table if needed and replaces data on materialization.

<CodeExample path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/io_manager/basic_example.py" />

### Step 3: Load upstream tables in downstream assets

Pass the upstream asset as a typed input; Dagster loads the table as a DataFrame.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/io_manager/load_downstream.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Completed example (I/O manager)

<CodeExample path="docs_snippets/docs_snippets/integrations/clickhouse/tutorial/io_manager/full_example.py" />

## Polars

Configure <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_polars" object="ClickhousePolarsIOManager" /> the same way as the Pandas I/O manager, and annotate assets with `pl.DataFrame` as inputs and outputs. Install **`dagster-clickhouse-polars`**.

## Templated SQL with `dg` and `ClickhouseQueryComponent`

To define templated SQL assets alongside a reusable ClickHouse connection in a [components](/guides/build/components) project, use <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseQueryComponent" /> with <PyObject section="components" module="dagster" object="TemplatedSqlComponent" />. See [ClickHouse SQL component](/integrations/libraries/clickhouse/clickhouse-sql-component).

## Related

- [ClickHouse integration reference](/integrations/libraries/clickhouse/reference)
- [I/O managers](/guides/build/io-managers)
- [Resources](/guides/build/external-resources)
