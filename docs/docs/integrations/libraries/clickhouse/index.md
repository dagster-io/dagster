---
title: Dagster & ClickHouse
sidebar_label: ClickHouse
sidebar_position: 1
description: This library provides an integration with ClickHouse using the native protocol (clickhouse-driver). Use a resource for ad hoc SQL, I/O managers for Pandas or Polars DataFrames, and components to wire templated SQL into Dagster projects with dg.
tags: [dagster-supported, storage]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-clickhouse
pypi: https://pypi.org/project/dagster-clickhouse/
sidebar_custom_props:
  logo: images/guides/build/assets/metadata-tags/kinds/icons/tool-clickhouse-color.svg
partnerlink: https://clickhouse.com/
canonicalUrl: '/integrations/libraries/clickhouse'
slug: '/integrations/libraries/clickhouse'
---

<p>{frontMatter.description}</p>

## Installation

Install the packages that match how you plan to use ClickHouse:

<PackageInstallInstructions packageName="dagster-clickhouse dagster-clickhouse-pandas dagster-clickhouse-polars" />

- **`dagster-clickhouse`**: <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseResource" />, <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseIOManager" />, and <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseQueryComponent" /> for `dg` projects.
- **`dagster-clickhouse-pandas`**: <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_pandas" object="ClickhousePandasIOManager" /> for Pandas DataFrames.
- **`dagster-clickhouse-polars`**: <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse_polars" object="ClickhousePolarsIOManager" /> for Polars DataFrames.

You will also need a running ClickHouse server (for example [ClickHouse Cloud](https://clickhouse.cloud/) or a self-hosted instance) reachable at the host and port you configure.

## Example

This example stores a Pandas DataFrame in ClickHouse using the Pandas I/O manager. Dagster maps the asset name to a **table** and uses the I/O manager **`schema`** (and optional asset `key_prefix`) to choose the **ClickHouse database** for that table.

<CodeExample path="docs_snippets/docs_snippets/integrations/clickhouse.py" language="python" />

## About ClickHouse

**ClickHouse** is a column-oriented OLAP database designed for analytical queries over large datasets. The Dagster integration connects with the **native protocol** (default port **9000**) using [`clickhouse-driver`](https://clickhouse-driver.readthedocs.io/).

### Dagster `schema` and ClickHouse databases

Unlike some databases, ClickHouse does not use a separate “schema” layer above the database. In this integration, Dagster’s **`schema` metadata and I/O manager `schema` config refer to a ClickHouse database name** (for example, `analytics` → `` `analytics`.`my_table` ``).

See the [Using ClickHouse with Dagster](/integrations/libraries/clickhouse/using-clickhouse-with-dagster) guide and the [reference](/integrations/libraries/clickhouse/reference) for usage patterns, including templated SQL with [`dg`](/guides/build/components).
