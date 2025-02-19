---
title: "Asset selection syntax"
sidebar_position: 1000
---

Dagster's asset selection syntax allows you to query and view assets within your data lineage graph. You can select upstream and downstream layers of the graph, use filters to narrow down your selection, and use functions to return the root or sink assets of a given selection.

With asset selection, you can:

- Select a set of assets to view in the Dagster UI
- Define a job in Python that targets a selection of assets
- List or materialize a set of assets using the [Dagster CLI](/api/python-api/cli#dagster-asset)


## Basic syntax

An **asset** is an entity within your data lineage graph, such as a table, dataset, or data pipeline.

| Asset selection | Syntax | Description |
|------|--------|-------------|
| Show a specific asset | `key:"my_asset"` | Select only the asset named `my_asset` in the graph. |

:::note Selecting all assets

To display the entire asset graph, you can use the `*` syntax. However, this is not a common use case, and we recommend refining your asset selection with the other syntax described in this reference.

:::

## Upstream and downstream layers

Filtering by upstream and downstream layers can help you understand the data flow within your assets.

- **Upstream assets** provide input to a given asset.
- **Downstream assets** receive input from a given asset.
- A **layer** is a level of connection in the graph. One layer up or down means a direct connection, "two layers" means connections two steps away, and so on.

### Upstream layers

| Asset selection | Syntax | Description |
|------|--------|-------------|
| One layer upstream of a particular asset | `1+key:"my_asset"` | Selects assets that directly provide input to `my_asset`. |
| Two layers upstream of a particular asset | `2+key:"my_asset"` | Selects assets two steps upstream from `my_asset`. |
| All layers upstream of a particular asset | `+key:"my_asset"` | Selects all upstream assets that provide input into `my_asset`. |


### Downstream layers

| Asset selection | Syntax | Description |
|------|--------|-------------|
| One layer downstream of a particular asset | `key:"my_asset"+1` | Selects assets that directly receive input from `my_asset`. |
| Two layers downstream of a particular asset | `key:"my_asset"+2` | Selects assets two steps downstream from `my_asset`. |
| All layers downstream of a particular asset | `key:"my_asset"+` | Selects all downstream assets that depend on `my_asset`. |

## Combining upstream and downstream

You can display both upstream and downstream layers simultaneously to get a comprehensive view of an asset's connections.

| Asset selection | Syntax | Description |
|-----------------|--------|-------------|
| One layer upstream and downstream of a particular asset | `1+key:"my_asset"+1` | Selects one layer of assets providing input to and receiving input from `my_asset`. |
| Two layers upstream and downstream of a particular asset | `2+key:"my_asset"+2` | Selects two layers of assets providing input to and receiving input from `my_asset`. |
| All layers upstream and downstream of a particular asset | `+key:"my_asset"+ ` | Selects all assets upstream and downstream of `my_asset`. |

## Filters

Filters allow you to narrow your asset selection using specific criteria.

| Filter | Syntax | Description |
|--------|--------|-------------|
| Exact key | `key:"my_key"` | Selects assets with the exact key `my_key`. |
| Tag | `tag:"stage"` | Selects assets tagged with `stage`. |
| Tag with value | `tag:"stage"="value"` | Selects assets tagged with `stage` having a specific `value`. |
| Owner | `owner:"alice"` | Selects assets owned by `alice`. |
| Group | `group:"team1"` | Selects assets in the group `team1`. |
| Kind |  `kind:"table"` |  Selects assets of kind `table`. |
| Code location | `code_location:"repo1"` | Selects assets located in code location `repo1`. |

### Combining filters with operands

You can combine multiple filters with operands to further refine your asset selection.

| Operand | Example | Description |
|---------|--------|-------------|
| `and` | `owner:"alice" and kind:"dbt"` | Selects assets owned by `alice` of kind `dbt`. |
| `or` | `owner:"billing" or owner:"sales"` | Selects assets owned by either `billing` or `sales`. |
| `not` | `not tag:"obsolete"` | Excludes assets tagged with `obsolete`. |
| Parentheses `()` | `(owner:"alice" and kind:"table") or group:"analytics"` | Symbols `(` and `)` used to group expressions and control the order of evaluation in queries. This example selects assets that are both owned by `alice` and of kind `table`, or that belong to the `analytics` group. |

## Functions

Functions allow you to perform specific operations on your asset selection. You can use `sink()` and `root()` functions to return the sink and root assets of the specified expression.

- **Sink assets** are assets without any downstream dependencies (leaf nodes), which means they don't provide input to any other assets.
- **Root assets** are assets without any upstream dependencies (root nodes), which means no assets provide input to them.

| Function | Description |
|--------|-------------|
| `sinks(expr)` | Selects only "sink" assets from the specified expression. |
|  `roots(expr)` | Selects only "root" assets from the specified expression. |

## Example queries

Here are some practical examples of the Dagster asset selection syntax to help you understand how to use it effectively.

| Scenario | Example query | Description |
|---------|-------|-------------|
| Exclude specific tags | `owner:"billing" and not tag:"enterprise"` | Selects everything owned by `billing` **excluding** any assets tagged with `enterprise`. |
| Find the path(s) between two groups of assets | `group:"sensitive_data"* and *group:"public_data"` | Selects all assets on the paths from the `sensitive_data` group to the `public_data` group. |
| Select all "sink" | `sinks(*)` | Selects all sink assets in the entire graph. |
| Combined upstream and downstream layers with filters | `+key:"data_pipeline" and kind:"table"+` | Selects one layer upstream and one layer downstream of `data_pipeline`, limited to assets of kind `table`. |
| Using parentheses to group conditions | `(owner:"alice" and kind:"table") or group:"analytics"` | Selects assets that are either owned by `alice` and of kind `table`, **or** belong to the `analytics` group. |
| Using parentheses to group conditions | `not (tag:"obsolete" or tag:"deprecated") and key_substring:"data"` | Selects assets whose keys contain `data` and are **not** tagged as `obsolete` or `deprecated`. |
