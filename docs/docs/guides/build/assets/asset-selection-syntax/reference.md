---
title: "Syntax reference"
sidebar_position: 200
---

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
| **Column tag** | `column:tag: "my_tag"` | Selects assets tagged with `my_tag`. | Dagster+ only |
| **Columns** | `columns: "my_column"` | Selects assets with a column named `my_column`. | Dagster+ only |
| **Table name** | `table_name: "my_table"` | Selects assets with a table named `my_table`. | Dagster+ only |
| **Changed in branch** | `changed_in_branch: "my_branch"` | Selects assets changed in a branch named `my_branch`. | Dagster+ branch deployments only |

:::note Wildcard matching

Only the `key` filter supports wildcard matching.

:::

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
| **Grouping `()`** | `(owner:"alice" and kind:"table") or group:"analytics"` | Symbols `(` and `)` used to group expressions and control the order of evaluation in queries. This example selects assets that are both owned by `alice` and of kind `table`, or that belong to the `analytics` group. |

## Functions

You can use `sink()` and `root()` functions to return the sink and root assets of an asset selection.

- **Sink assets** are assets without any downstream dependencies (leaf nodes), which means they don't provide input to any other assets.
- **Root assets** are assets without any upstream dependencies (root nodes), which means no assets provide input to them.

| Function | Syntax | Description |
|--------|-------------|-----------|
| **`sinks(expr)`** | `sinks(expr)` | Selects only "sink" assets from the specified expression. |
| **`roots(expr)`** | `roots(expr)` | Selects only "root" assets from the specified expression. |
