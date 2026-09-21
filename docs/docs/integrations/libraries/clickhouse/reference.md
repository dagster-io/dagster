---
title: 'dagster-clickhouse integration reference'
description: Customize ClickHouse resources and I/O managers in Dagster.
sidebar_position: 200
---

This page covers ClickHouse integration details beyond the [Using ClickHouse with Dagster](/integrations/libraries/clickhouse/using-clickhouse-with-dagster) guide.

## ClickHouse resource

The <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseResource" /> exposes a [`clickhouse_driver.Client`](https://clickhouse-driver.readthedocs.io/en/latest/api.html#clickhouse_driver.Client) from `get_connection()`. Use it to run DDL/DML and queries with full control over SQL.

### Executing custom SQL

<CodeExample
  path="docs_snippets/docs_snippets/integrations/clickhouse/reference/resource.py"
  startAfter="start"
  endBefore="end"
/>

This builds on the `iris.iris_dataset` table created in the [resource tutorial](/integrations/libraries/clickhouse/using-clickhouse-with-dagster#option-1-using-the-clickhouse-resource).

## ClickHouse I/O managers

The Pandas and Polars I/O managers create **MergeTree** tables when needed and use **`ALTER TABLE … DELETE`** (with `mutations_sync = 1`) or **`TRUNCATE`** when replacing partitions or full tables, consistent with <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseDbClient" />.

### Selecting specific columns in a downstream asset

You can restrict loaded columns by attaching **`columns`** metadata on the input asset, similar to other database I/O managers:

<CodeExample path="docs_snippets/docs_snippets/integrations/clickhouse/reference/downstream_columns.py" />

### Dagster `schema` vs connection `database`

- **`schema` on the I/O manager / asset metadata**: the ClickHouse **database** that contains the table (for example `` `analytics`.`revenue_daily` ``).
- **`database` on the I/O manager / resource**: the default database **on the client session** (ClickHouse `USE` semantics). Table locations for assets still use the Dagster `schema` / asset metadata path.

### Legacy `@io_manager` factories

The packages expose `clickhouse_pandas_io_manager` and `clickhouse_polars_io_manager` built with <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="build_clickhouse_io_manager" /> for setups that prefer the older factory style.

## Related

- [ClickHouse integration packages](/integrations/libraries/clickhouse/dagster-clickhouse)
- [I/O managers](/guides/build/io-managers)
