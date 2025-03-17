---
title: "Asset selection syntax reference"
sidebar_position: 100
---

This page contains a full list of the filters, layers, operands, and functions you can use to construct your own asset selection queries. For a list of common queries, see "[Asset selection examples](/guides/build/assets/asset-selection-syntax/examples)".

## Filters

Filters allow you to narrow your asset selection using specific criteria.

| Filter | Syntax | Description | Supported views |
|--------|--------|-------------|-----------------|
| **Key (exact)** | `key:"my_asset"` | Selects assets with the exact key `my_asset`. | OSS, Dagster+, Dagster+ branch deployments |
| **Key with one wildcard** | `key:"prefix_*"`| Selects assets whose key starts with `prefix`. | OSS, Dagster+, Dagster+ branch deployments |
| **Key with multiple wildcards** | `key:"prefix_*_middlefix_*_suffix"` | Selects assets whose key starts with `prefix`, contains `middlefix`, and ends with `suffix`. | OSS, Dagster+, Dagster+ branch deployments |
| **Tag (exact)** | `tag:"stage"` | Selects assets tagged with `stage`. | OSS, Dagster+, Dagster+ branch deployments |
| **Tag (with value)** | `tag:"stage"="value"` | Selects assets tagged with `stage` having a specific `value`. | OSS, Dagster+, Dagster+ branch deployments |
| **Owner** | `owner:"alice"` | Selects assets owned by `alice`. | OSS, Dagster+, Dagster+ branch deployments |
| **Group** | `group:"team1"` | Selects assets in the group `team1`. | OSS, Dagster+, Dagster+ branch deployments |
| **Kind** |  `kind:"table"` |  Selects assets of kind `table`. | OSS, Dagster+, Dagster+ branch deployments |
| **Code location** | `code_location:"repo1"` | Selects assets located in code location `repo1`. | OSS, Dagster+, Dagster+ branch deployments |
| **Column tag** | `column_tag: "my_tag"` | Selects assets tagged with `my_tag`. | Dagster+ only |
| **Columns** | `columns: "my_column"` | Selects assets with a column named `my_column`. | Dagster+ only |
| **Table name** | `table_name: "my_table"` | Selects assets with a table named `my_table`. | Dagster+ only |


:::info Wildcard matching

Only the `key` filter supports wildcard matching.

:::

### `changed_in_branch` filter

The `changed_in_branch` filter selects assets that have been changed for a specific reason in a specific branch. The reason can be one of `ANY`, `CODE_VERSION`, `DEPENDENCIES`, `METADATA`, `NEW`, `PARTITIONS_DEFINITION`, or `TAGS`.

:::info

The `changed_in_branch` filter is only available in [Dagster+ branch deployments](/dagster-plus/features/ci-cd/branch-deployments/).

:::

| Reason | Syntax | Description |
|------------|--------|-------------|
| `ANY`      | `changed_in_branch: "ANY"` | Selects any assets changed in the branch. |
| `CODE_VERSION` | `changed_in_branch: "CODE_VERSION"` | Selects assets whose code version changed in the branch. |
| `DEPENDENCIES` | `changed_in_branch: "DEPENDENCIES"` | Selects assets whose dependencies changed in the branch. |
| `METADATA` | `changed_in_branch: "METADATA"`  | Selects assets whose metadata has changed in the branch. |
| `NEW` | `changed_in_branch: "NEW"` | Selects assets that are new in the branch. |
| `PARTITIONS_DEFINITION` | `changed_in_branch: "PARTITIONS_DEFINITION"` | Selects assets whose partitions definition has changed in the branch. |
| `TAGS` | `changed_in_branch: "TAGS"` | Selects assets whose tags have changed in the branch. |

## Upstream and downstream layers

Filtering by upstream and downstream layers can help you understand the data flow within your assets.

- **Upstream assets** provide input to a given asset.
- **Downstream assets** receive input from a given asset.
- A **layer** is a level of connection in the graph. One layer up or down means a direct connection, "two layers" means connections two steps away, and so on.

| Asset selection | Syntax | Description |
|------|--------|-------------|
| **All layers upstream of an asset** | `+key:"my_asset"` | Selects all upstream assets that provide input into `my_asset`. |
| **One layer upstream of an asset** | `1+key:"my_asset"` | Selects assets that directly provide input to `my_asset`. |
| **Two layers upstream of an asset** | `2+key:"my_asset"` | Selects assets two steps upstream from `my_asset`. |
| **All layers downstream of an asset** | `key:"my_asset"+` | Selects all downstream assets that depend on `my_asset`. |
| **One layer downstream of an asset** | `key:"my_asset"+1` | Selects assets that directly receive input from `my_asset`. |
| **Two layers downstream of an asset** | `key:"my_asset"+2` | Selects assets two steps downstream from `my_asset`. |
| **One layer upstream and downstream of an asset** | `1+key:"my_asset"+1` | Selects one layer of assets providing input to and receiving input from `my_asset`. |
| **Two layers upstream and downstream of an asset** | `2+key:"my_asset"+2` | Selects two layers of assets providing input to and receiving input from `my_asset`. |
| **All layers upstream and downstream of an asset** | `+key:"my_asset"+` | Selects all assets upstream and downstream of `my_asset`. |

## Operands and grouping

You can combine multiple filters with operands and group them with parentheses to further refine your asset selection:

| Operand | Syntax | Description |
|---------|--------|-------------|
| **`and`** | `owner:"alice" and kind:"dbt"` | Selects assets owned by `alice` of kind `dbt`. |
| **`or`** | `owner:"billing" or owner:"sales"` | Selects assets owned by either `billing` or `sales`. |
| **`not`** | `not tag:"obsolete"` | Excludes assets tagged with `obsolete`. |
| **Grouping `()`** | `(owner:"alice" or group:"analytics") and  kind:"table"` | Symbols `(` and `)` used to group expressions and control the order of evaluation in queries. This example selects assets that are both owned by `alice` and of kind `table`, or that belong to the `analytics` group. |

## Functions

You can use `roots(selection)` and `sinks(selection)` functions to return the sink or root assets of an asset selection.

- **Root assets** are assets that have no upstream dependencies within the asset selection. Root assets can have upstream dependencies outside of the asset selection.

- **Sink assets** are assets that have no downstream dependencies within the asset selection. Sink assets can have downstream dependencies outside of the asset selection.

| Example | Description |
|--------|--------------|
| `roots(*)` | Select all assets without any upstream dependencies. |
| `sinks(*)` | Select all assets without any downstream dependencies. |
| `roots(group:"public_data")` | Selects root assets within the `public_data` group.|
| `sinks(group:"public_data")` | Selects sink assets within the `public_data` group. |
| `roots(+group:"public_data")` | Selects all root assets that feed into the `public_data` group. |
| `sinks(group:"public_data"+)` | Selects all sink assets that depend on assets in the `public_data` group. |
