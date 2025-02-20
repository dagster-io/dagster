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

| Asset selection | Example | Description |
| --- | --- | --- |
| **Specific asset** | `key:"my_asset"` | Selects assets with key `my_key`. |
| **Entire graph** | `*` | Displays all assets and connections. |

### Examples

#### Select a single asset \{#single-asset}

An **asset** is an entity within your data lineage graph, such as a table, dataset, or data pipeline.

To select a single asset, use the asset's asset key. This example selects the `taxi_zones_file` asset:

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
taxi_zones_file = AssetSelection.from_string('key:"taxi_zones_file"')
```

</TabItem>
<TabItem value="cli" label="CLI">

```shell
dagster asset list --select 'key:"taxi_zones_file"'
dagster asset materialize --select 'key:"taxi_zones_file"'
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select assets with multiple key components \{#multiple-key-components}

To select an asset with a key containing multiple components, such as a prefix, insert slashes (`/`) between the components.

This example selects the `manhattan/manhattan_stats` asset, which is defined below:

```python
@asset(
    deps=[AssetKey(["taxi_trips"]), AssetKey(["taxi_zones"])], key_prefix="manhattan"
)
def manhattan_stats(database: DuckDBResource):
 ...
```

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
manhattan_stats = AssetSelection.from_string('key:"manhattan/manhattan_stats"')
```

</TabItem>
<TabItem value="cli" label="CLI">

```shell
dagster asset list --select 'key:"manhattan/manhattan_stats"'
dagster asset materialize --select 'key:"manhattan/manhattan_stats"'
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
manhattan/manhattan_stats
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select multiple assets \{#multiple-assets}

TODO how would you do this in new syntax?

To select multiple assets, use a list of the assets' asset keys. The assets don't have to be dependent on each other.

This example selects the `taxi_zones_file` and `taxi_trips_file` assets, which are defined below:

<Tabs groupId="examples">
<TabItem value="python" label="Python">

When selecting multiple assets, enclose the list of asset keys in double quotes (`"`) and separate each asset key with a comma:

```python
taxi_zones_and_trips = AssetSelection.from_string("taxi_zones_file, taxi_trips_file")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting multiple assets, enclose the list of asset keys in double quotes (`"`) and separate each asset key with a comma:

```shell
dagster asset list --select "taxi_zones_file,taxi_trips_file"
dagster asset materialize --select "taxi_zones_file,taxi_trips_file"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file taxi_trips_file
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

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
| **All layers upstream and downstream of an asset** | `+key:"my_asset"+ ` | Selects all assets upstream and downstream of `my_asset`. |

### Examples

#### Select all upstream layers \{#all-upstream}

To select an asset and all its upstream dependencies, add a plus sign (`+`) before the asset key in the query.

This example selects the `manhattan_map` asset and all its upstream dependencies.

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
manhattan_all_upstream = AssetSelection.from_string("+manhattan_map")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's entire lineage using the CLI, enclose the plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "+manhattan_map"
dagster asset materialize --select "+manhattan_map"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
+manhattan_map
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select a specific number of upstream layers \{#specific-upstream}

To select an asset and multiple upstream layers, add a number and plus sign (`+`) for the layers you want to select before the asset key in the query.

This example selects the `manhattan_map` asset and two upstream layers.

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
manhattan_two_upstream = AssetSelection.from_string("2+manhattan_map")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the number and plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "2+manhattan_map"
dagster asset materialize --select "2+manhattan_map"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
2+manhattan_map
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select all downstream layers \{#all-downstream}

To select an asset and all its downstream dependencies, add a plus sign (`+`) after the asset key in the query.

This example selects the `taxi_zones_file` asset and all its downstream dependencies.

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
taxi_zones_all_downstream = AssetSelection.from_string("taxi_zones_file+")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "taxi_zones_file*"
dagster asset materialize --select "taxi_zones_file+"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file+
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select a specific number of downstream layers \{#specific-downstream}

To select an asset and multiple downstream layers, add a number and plus sign (`+`) for the layer you want to select after the asset key in the query.

This example selects the `taxi_trips_file` asset and two downstream layers.

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
taxi_jobs_two_downstream = AssetSelection.from_string("taxi_zones_file+2")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the number and plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "taxi_zones_file+2"
dagster asset materialize --select "taxi_zones_file+2"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file++
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

#### Select all upstream and downstream layers \{#full-lineage}

To select an asset's entire lineage (all upstream and downstream layers), add a plus sign (`+`) before and after the asset key in the query.

This example selects the entire lineage for the `taxi_zones` asset.

<Tabs groupId="examples">
<TabItem value="python" label="Python">

```python
taxi_zones_all = AssetSelection.from_string("+taxi_zones+")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's entire lineage using the CLI, enclose the plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "+taxi_zones+"
dagster asset materialize --select "+taxi_zones+"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
+taxi_zones+
```

Which would result in the following asset graph:

{/* TODO: Add screenshot ![]() */}

</TabItem>
</Tabs>

## Filters, operands, and grouping

Filters allow you to narrow your asset selection using specific criteria.

| Filter | Syntax | Description | Supported views |
|--------|--------|-------------|-----------------|
| **Exact key** | `key:"my_key"` | Selects assets with the exact key `my_key`. | OSS, Dagster+, Dagster+ branch deployments |
| **Key substring with wildcard filter** | `key:partial_key_*`| Selects assets whose key contains `partial_key`. | OSS, Dagster+, Dagster+ branch deployments |
| **Tag (exact)** | `tag:"stage"` | Selects assets tagged with `stage`. | OSS, Dagster+, Dagster+ branch deployments |
| **Tag (with value)** | `tag:"stage"="value"` | Selects assets tagged with `stage` having a specific `value`. | OSS, Dagster+, Dagster+ branch deployments |
| **Owner** | `owner:"alice"` | Selects assets owned by `alice`. | OSS, Dagster+, Dagster+ branch deployments |
| **Group** | `group:"team1"` | Selects assets in the group `team1`. | OSS, Dagster+, Dagster+ branch deployments |
| **Kind** |  `kind:"table"` |  Selects assets of kind `table`. | OSS, Dagster+, Dagster+ branch deployments |
| **Code location** | `code_location:"repo1"` | Selects assets located in code location `repo1`. | OSS, Dagster+, Dagster+ branch deployments |
| **Column tag** | `column:tag: "my_tag"` | TODO | Dagster+ |
| **Columns** | `columns: "column_name"` | TODO | Dagster+ |
| **Table name** | `table_name: "my_table"` | TODO | Dagster+ |
| **Changed in branch** | `changed_in_branch: | TODO | Dagster+ branch deployments |

:::note Wildcard matching in the `key` filter

Only the `key` filter supports wildcard matching.

:::

You can combine multiple filters with operands to further refine your asset selection:

| Operand | Example | Description |
|---------|--------|-------------|
| **`and`** | `owner:"alice" and kind:"dbt"` | Selects assets owned by `alice` of kind `dbt`. |
| **`or`** | `owner:"billing" or owner:"sales"` | Selects assets owned by either `billing` or `sales`. |
| **`not`** | `not tag:"obsolete"` | Excludes assets tagged with `obsolete`. |
| **Grouping with parentheses `()`** | `(owner:"alice" and kind:"table") or group:"analytics"` | Symbols `(` and `)` used to group expressions and control the order of evaluation in queries. This example selects assets that are both owned by `alice` and of kind `table`, or that belong to the `analytics` group. |

### Examples

#### Select upstream and downstream assets with filters \{#filters}

```shell
+key:"data_pipeline" and kind:"table"+
```

Selects one layer upstream and one layer downstream of `data_pipeline`, limited to assets of kind `table`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK - Python
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

#### Select assets without specific tags \{#not-tag}

```shell
owner:"billing" and not tag:"enterprise"
```

Selects everything owned by `billing` **excluding** any assets tagged with `enterprise`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    billing_assets = AssetSelection.from_string('owner:"billing" and not tag:"enterprise"')
    ```
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select owner:"billing" and not tag:"enterprise"
    ```
    </TabItem>
</Tabs>

#### Select all assets on the path between two groups of assets \{#asset-path}

```shell
group:"sensitive_data"* and *group:"public_data"
```

Selects all assets on the paths from the `sensitive_data` group to the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK - Python
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

#### Select assets with parentheses grouping and filters \{#grouping-filters}

##### Example 1

```shell
(owner:"alice" and kind:"table") or group:"analytics"
```

Selects assets that are either owned by `alice` and of kind `table`, **or** belong to the `analytics` group.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

##### Example 2

```shell
not (tag:"obsolete" or tag:"deprecated") and key_substring:"data"
```

Selects assets whose keys contain `data` and are **not** tagged as `obsolete` or `deprecated`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK - Python
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

## Functions

Functions allow you to perform specific operations on your asset selection. You can use `sink()` and `root()` functions to return the sink and root assets of the specified expression.

- **Sink assets** are assets without any downstream dependencies (leaf nodes), which means they don't provide input to any other assets.
- **Root assets** are assets without any upstream dependencies (root nodes), which means no assets provide input to them.

| Function | Example | Description |
|--------|-------------|-----------|
| **`sinks(expr)`** | `sinks(*)` | Selects only "sink" assets from the specified expression. |
| **`roots(expr)`** | `roots(*)` | Selects only "root" assets from the specified expression. |

### TODO sinks example \{#sinks}

More sophisticated example here (not just `sinks(*)`)

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK - Python
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

### TODO roots example \{#roots}

More sophisticated example here (not just `roots(*)`)

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TK - Python
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TK - UI
    </TabItem>
    <TabItem value="cli" label="CLI">
        TK - CLI
    </TabItem>
</Tabs>

