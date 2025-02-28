---
title: 'Asset selection examples'
sidebar_position: 100
---

This page contains common example asset selection queries and their implementation in Python, CLI, and the Dagster UI. For a full explanation of the filters, layers, operands, and functions that you can use to construct your own queries, see "[Asset selection syntax reference](reference)".

## Select all assets on the path between two assets

```shell
key:"taxi_trips_file"+ and +key:"manhattan_stats"
```

Selects all assets on the path from the `taxi_trips_file` asset to the `manhattan_stats` asset.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    taxi_trips_manhattan_stats_job = define_asset_job(
        name="taxi_trips_manhattan_stats_job", selection='key:"taxi_trips_file"+ and +key:"manhattan_stats"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"taxi_trips_file"+ and +key:"manhattan_stats"'
    dagster asset materialize --select 'key:"taxi_trips_file"+ and +key:"manhattan_stats"'
    ```
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
    ```shell
    key:"taxi_trips_file"+ and +key:"manhattan_stats"
    ```

    Which would result in the following asset graph:
    {/* TODO: Nikki to add screenshot ![]() */}
    </TabItem>
</Tabs>

## Select all assets on the path between two sets of assets

```shell
(key:"start-1" or key:"start-2")+ and +(key:"end-1" or key:"end-2")
```

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>

## Select all assets on the path between two sets of assets by tag

```shell
tag:"private"+ and +tag:"public"
```

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>

## Select all assets on the path between two groups of assets \{#asset-path}

```shell
group:"sensitive_data"* and *group:"public_data"
```

Selects all assets on the paths from the `sensitive_data` group to the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>

## Select assets between two assets that go through the "middle" asset

```shell
key:"taxi_zones_file"+ and +key:"manhattan_stats"+ and +key:"manhattan_map"
```

Selects all assets on the path between the `taxi_zones_file` asset and `manhattan_map` asset that go through the `manhattan_stats` asset.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    taxi_zones_stats_map_job = define_asset_job(
        name="taxi_zones_stats_map_job", selection='key:"taxi_zones_file"+ and +key:"manhattan_stats"+ and +key:"manhattan_map"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    dagster asset list --select 'key:"taxi_zones_file"+ and +key:"manhattan_stats"+ and +key:"manhattan_map"'
    dagster asset materialize --select 'key:"taxi_zones_file"+ and +key:"manhattan_stats"+ and +key:"manhattan_map"'
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
    ```shell
    key:"taxi_zones_file"+ and +key:"manhattan_stats"+ and +key:"manhattan_map"
    ```

    Which would result in the following asset graph:
    {/* TODO: Nikki to add screenshot ![]() */}
    </TabItem>
</Tabs>

## Select assets with multiple key components \{#multiple-key-components}

To select an asset with a key containing multiple components, such as a prefix, insert slashes (`/`) between the components.

This example selects the `manhattan/manhattan_stats` asset, which is defined below:

```python
@dg.asset(
    deps=[dg.AssetKey(["taxi_trips"]), dg.AssetKey(["taxi_zones"])],
    key_prefix="manhattan",
    ...
)
def manhattan_stats(database: DuckDBResource) -> None:
    ...
```

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    manhattan_job = define_asset_job(name="manhattan_job", selection='key:"manhattan/manhattan_stats"')
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

    {/* TODO: Nikki to add screenshot ![]() */}

</TabItem>
</Tabs>

## Select multiple assets with `or` \{#multiple-assets}

To select multiple assets, use the `or` operand. The assets don't have to be dependent on each other.

This example selects the `taxi_zones_file` and `taxi_trips_file` assets, which are defined below:

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    raw_data_job = define_asset_job(
        name="raw_data_job", selection='key:"taxi_zones_file" or key:"taxi_trips_file"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"taxi_zones_file" or key:"taxi_trips_file"'
    dagster asset materialize --select 'key:"taxi_zones_file" or key:"taxi_trips_file"'
    ```
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
    ```shell
    key:"taxi_zones_file" or key:"taxi_trips_file"
    ```
    Which would result in the following asset graph:

    {/* TODO: Nikki to add screenshot ![]() */}

</TabItem>
</Tabs>

## Select upstream and downstream assets with filters \{#filters}

```shell
+key:"manhattan_stats" and kind:"duckdb"+
```

Selects one layer upstream and one layer downstream of `manhattan_stats`, limited to assets of kind `duckdb`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    manhattan_stats_duckdb_job = define_asset_job(
        name="manhattan_stats_duckdb_job", selection='+key:"manhattan_stats" and kind:"duckdb"+'
    )
   ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select '+key:"manhattan_stats" and kind:"duckdb"+'
    dagster asset materialize --select '+key:"manhattan_stats" and kind:"duckdb"+'
    ```
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">

    ```shell
    +key:"manhattan_stats" and kind:"duckdb"+
    ```

    Which would result in the following asset graph:
    {/* TODO: Nikki to add screenshot ![]() */}
    </TabItem>
</Tabs>

## Select assets without specific tags \{#not-tag}

```shell
owner:"team:data_eng" and not tag:"source"="nyc_open_data_portal"
```

Selects everything owned by team `data_eng` **excluding** any assets tagged with `source=nyc_open_data_portal`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    data_eng_not_nyc_data_portal_job = define_asset_job(
        name="data_eng_not_nyc_data_portal_job", selection='owner:"team:data_eng" and not tag:"source"="nyc_open_data_portal"'
    )
    billing_assets = AssetSelection.from_string('owner:"billing" and not tag:"enterprise"')
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'owner:"team:data_eng" and not tag:"source"="nyc_open_data_portal"'
    dagster asset materialize --select 'owner:"team:data_eng" and not tag:"source"="nyc_open_data_portal"'
    ```
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
    ```shell
    owner:"team:data_eng" and not tag:"source"="nyc_open_data_portal"
    ```

    Which would result in the following asset graph:
    {/* TODO: Nikki to add screenshot ![]() */}
    </TabItem>
</Tabs>

## Select assets with parentheses grouping and filters \{#grouping-filters}

### Select a parentheses group `or` assets that belong in a specific `group`

```shell
(owner:"ada.dagster@example.com" and kind:"csv") or group:"analytics"
```

Selects assets that are either owned by `ada.dagster@example.com` and of kind `csv`, **or** that belong to the `analytics` group.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
    ```python
    ada_csv_analytics_job = define_asset_job(
        name="ada_csv_analytics_job", selection='(owner:"ada.dagster@example.com" and kind:"csv") or group:"analytics"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    dagster asset list --select '(owner:"ada.dagster@example.com" and kind:"csv") or group:"analytics"'
    dagster asset materialize --select '(owner:"ada.dagster@example.com" and kind:"csv") or group:"analytics"'
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
    ```shell
    (owner:"ada.dagster@example.com" and kind:"csv") or group:"analytics"
    ```

    Which would result in the following asset graph:
    {/* TODO: Nikki to add screenshot ![]() */}
    </TabItem>
</Tabs>

### Exclude a parentheses group with `not` and select assets that match a `key` wildcard

```shell
not (tag:"obsolete" or tag:"deprecated") and key:"data*"
```

Selects assets whose keys contain `data` and are **not** tagged as `obsolete` or `deprecated`.

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>

## Select all sink assets \{#sinks}

```shell
sinks(*)
```

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>

## Select all root assets \{#roots}

```shell
roots(*)
```

<Tabs groupId="examples">
    <TabItem value="python" label="Python">
        TODO
    </TabItem>
    <TabItem value="cli" label="CLI">
        TODO
    </TabItem>
    <TabItem value="dagster-ui" label="Dagster UI">
        TODO
    </TabItem>
</Tabs>