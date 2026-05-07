---
title: ClickHouse SQL component
sidebar_position: 300
description: Run templated SQL against ClickHouse with Dagster components and dg.
tags: [dagster-supported, storage, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-clickhouse
pypi: https://pypi.org/project/dagster-clickhouse/
sidebar_custom_props:
  logo: images/guides/build/assets/metadata-tags/kinds/icons/tool-clickhouse-color.svg
partnerlink: https://clickhouse.com/
---

Dagster’s <PyObject section="components" module="dagster" object="TemplatedSqlComponent" /> runs SQL through a connection object.
The <PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseQueryComponent" />
(in **`dagster-clickhouse`**) supplies a ClickHouse connection compatible with that workflow so you can
scaffold a reusable connection and reference it from templated SQL definitions.

:::info

<PyObject section="libraries" integration="clickhouse" module="dagster_clickhouse" object="ClickhouseQueryComponent" />
is currently **preview**. Behavior and configuration may change in minor releases.

:::

## Step 1: Prepare a Dagster project

Use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

Add the ClickHouse library:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/2-add-clickhouse.txt" />

## Step 2: Scaffold a templated SQL component

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/3-scaffold-sql-component.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/4-tree.txt" />

## Step 3: Scaffold a ClickHouse connection component

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/6-scaffold-connection-component.txt" />

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/7-connection-component.yaml"
  title="my_project/defs/clickhouse_connection/defs.yaml"
  language="yaml"
/>

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/8-tree.txt" />

You typically keep **one** connection component per ClickHouse cluster and reuse it from multiple SQL components.

## Step 4: Point templated SQL at the connection

Update the templated SQL `defs.yaml` to load the connection component and provide ClickHouse-specific SQL. This example aggregates the Iris dataset by species:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/9-customized-component.yaml"
  title="my_project/defs/species_counts/defs.yaml"
  language="yaml"
/>

You can list the resulting defs with:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/10-list-defs.txt" />

## Step 5: Launch your assets

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/clickhouse-sql-component/11-launch.txt" />

## Related

- [Using ClickHouse with Dagster](/integrations/libraries/clickhouse/using-clickhouse-with-dagster)
- [Snowflake SQL component](/integrations/libraries/snowflake/snowflake-sql-component) (same `TemplatedSqlComponent` pattern)
