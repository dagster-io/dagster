---
title: 'Asset selection syntax'
sidebar_position: 70
sidebar_label: 'Asset selection syntax'
---

# Asset selection syntax

This reference contains information about the syntax for asset selections, including a variety of examples for selecting assets and their downstream and upstream dependencies.

Asset selection may be used to:

- Define a job that targets a selection of assets
- Select a set of assets to view in the Dagster UI
- Select a set of assets for an adhoc run

## Syntax usage

A query includes a list of clauses. Clauses are separated by commas, except in the case of the `selection` parameter of the following methods. In these cases, each clause is a separate element in a list:

- `define_asset_job`
- `materialize`
- `materialize_to_memory`

| Clause syntax         | Description                                                                                                                                                                                                                                                                                                               |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ASSET_KEY`           | Selects a single asset by asset key. [See an example](#single-asset).                                                                                                                                                                                                                                                                                       |
| `COMPONENT/COMPONENT` | Selects an asset key with multiple components, such as a prefix, where slashes (`/`) are inserted between components. [See an example](#multiple-key-components).                    |
| `*ASSET_KEY`          | Selects an asset and all of its upstream dependencies. [See an example](#all-upstream).                                                                                                                                                                                                                             |
| `ASSET_KEY*`          | Selects an asset and all of its downstream dependencies. [See an example](#all-downstream).                                                                                                                                                                                                                           |
| `+ASSET_KEY`          | Selects an asset and one layer upstream of the asset. Including multiple `+`s will select that number of upstream layers from the asset. Any number of `+`s is supported. [See an example](#specific-upstream).    |
| `ASSET_KEY+`          | Selects an asset and one layer downstream of the asset. Including multiple `+`s will select that number of downstream layers from the asset. Any number of `+`s is supported. [See an example](#specific-downstream). |

## Examples

The examples in this section use the following asset graph from the [Dagster University Essentials project](https://github.com/dagster-io/project-dagster-university) to demonstrate how to use the selection syntax:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

### Selecting a single asset \{#single-asset}

To select a single asset, use the asset's asset key. This example selects the `taxi_zones_file` asset:

<Tabs>
<TabItem value="python" label="Python">

```python
raw_data_job = define_asset_job(name="raw_data_job", selection="taxi_zones_file")
```

</TabItem>
<TabItem value="cli" label="CLI">

```shell
dagster asset list --select taxi_zones_file
dagster asset materialize --select taxi_zones_file
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

---

### Selecting assets with multiple key components \{#multiple-key-components}

To select an asset with a key containing multiple components, such as a prefix, insert slashes (`/`) between the components.

This example selects the `manhattan/manhattan_stats` asset, which is defined below:

```python
@asset(
    deps=[AssetKey(["taxi_trips"]), AssetKey(["taxi_zones"])], key_prefix="manhattan"
)
def manhattan_stats(database: DuckDBResource):
 ...
```

<Tabs>
<TabItem value="python" label="Python">

```python
manhattan_job = define_asset_job(name="manhattan_job", selection="manhattan/manhattan_stats")
```

</TabItem>
<TabItem value="cli" label="CLI">

```shell
dagster asset list --select manhattan/manhattan_stats
dagster asset materialize --select manhattan/manhattan_stats
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
manhattan/manhattan_stats
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

---

### Selecting multiple assets \{#multiple-assets}

To select multiple assets, use a list of the assets' asset keys. The assets don't have to be dependent on each other.

This example selects the `taxi_zones_file` and `taxi_trips_file` assets, which are defined below:

<Tabs>
<TabItem value="python" label="Python">

```python
raw_data_job = define_asset_job(
    name="taxi_zones_job", selection=["taxi_zones_file", "taxi_trips_file"]
)
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

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

---

### Selecting an asset's entire lineage \{#full-lineage}

To select an asset's entire lineage, add an asterisk (`*`) before and after the asset key in the query.

This example selects the entire lineage for the `taxi_zones` asset.

<Tabs>
<TabItem value="python" label="Python">

```python
taxi_zones_job = define_asset_job(name="taxi_zones_job", selection="*taxi_zones*")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's entire lineage using the CLI, enclose the asterisk (`*`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "*taxi_zones*"
dagster asset materialize --select "*taxi_zones*"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
*taxi_zones*
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

---

### Selecting upstream dependencies

#### Selecting all upstream dependencies \{#all-upstream}

To select an asset and all its upstream dependencies, add an asterisk (`*`) before the asset key in the query.

This example selects the `manhattan_map` asset and all its upstream dependencies.

<Tabs>
<TabItem value="python" label="Python">

```python
manhattan_job = define_asset_job(name="manhattan_job", selection="*manhattan_map")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the asterisk (`*`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "*manhattan_map"
dagster asset materialize --select "*manhattan_map"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
*manhattan_map
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

#### Selecting a specific number of upstream layers \{#specific-upstream}

To select an asset and multiple upstream layers, add a plus sign (`+`) for each layer you want to select before the asset key in the query.

This example selects the `manhattan_map` asset and two upstream layers.

<Tabs>
<TabItem value="python" label="Python">

```python
manhattan_job = define_asset_job(name="manhattan_job", selection="++manhattan_map")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "++manhattan_map"
dagster asset materialize --select "++manhattan_map"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
++manhattan_map
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

---

### Selecting downstream dependencies

#### Selecting all downstream dependencies \{#all-downstream}

To select an asset and all its downstream dependencies, add an asterisk (`*`) after the asset key in the query.

This example selects the `taxi_zones_file` asset and all its downstream dependencies.

<Tabs>
<TabItem value="python" label="Python">

```python
taxi_zones_job = define_asset_job(name="taxi_zones_job", selection="taxi_zones_file*")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the asterisk (`*`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "taxi_zones_file*"
dagster asset materialize --select "taxi_zones_file*"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file*
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>

#### Selecting a specific number of downstream layers \{#specific-downstream}

To select an asset and multiple downstream layers, add plus sign (`+`) for each layer you want to select after the asset key in the query.

This example selects the `taxi_trips_file` asset and two downstream layers.

<Tabs>
<TabItem value="python" label="Python">

```python
taxi_zones_job = define_asset_job(name="taxi_zones_job", selection="taxi_zones_file++")
```

</TabItem>
<TabItem value="cli" label="CLI">

When selecting an asset's dependencies using the CLI, enclose the plus sign (`+`) and the asset key in double quotes (`"`):

```shell
dagster asset list --select "taxi_zones_file++"
dagster asset materialize --select "taxi_zones_file++"
```

</TabItem>
<TabItem value="dagster-ui" label="Dagster UI">

```shell
taxi_zones_file++
```

Which would result in the following asset graph:

![Screenshot of Daggy U project graph](/img/placeholder.svg)

</TabItem>
</Tabs>
