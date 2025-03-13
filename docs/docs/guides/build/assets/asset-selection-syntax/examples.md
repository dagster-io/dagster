---
title: 'Asset selection examples'
sidebar_position: 200
---

This page contains common example asset selection queries and their implementation in Python, CLI, and the Dagster UI. For a full explanation of the filters, layers, operands, and functions that you can use to construct your own queries, see "[Asset selection syntax reference](/guides/build/assets/asset-selection-syntax/reference)".

The examples in this section use the following asset graph to demonstrate how to use the selection syntax:

![ExampleCo asset lineage](/images/guides/build/assets/asset-selection-syntax/exampleco-global-asset-lineage.png)

## Select all assets on the path between two assets

```shell
key:"raw_data_b"+ and +key:"summary_stats_2"
```

Selects all assets on the path from the `raw_data_b` asset to the `summary_stats_2` asset.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![All assets on the path between two assets](/images/guides/build/assets/asset-selection-syntax/select-assets-between-two-assets.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    raw_data_b_summary_stats_2_job = define_asset_job(
        name="raw_data_b_summary_stats_2_job", selection='key:"raw_data_b"+ and +key:"summary_stats_2"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"raw_data_b"+ and +key:"summary_stats_2"'
    dagster asset materialize --select 'key:"raw_data_b"+ and +key:"summary_stats_2"'
    ```
    </TabItem>
</Tabs>

## Select all assets on the path between two sets of assets

```shell
(key:"raw_data_a" or key:"raw_data_b")+ and +(key:"a_b_c_for_sales" or key:"b_c_for_sales")
```

Selects all assets on the paths between the `raw_data_a` or `raw_data_b` assets and the `a_b_c_for_sales` and `b_c_for_sales` assets.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![All assets between two sets of assets](/images/guides/build/assets/asset-selection-syntax/select-assets-between-two-sets-of-assets.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    assets_on_path_job = define_asset_job(
        name="assets_on_path_job", selection='(key:"raw_data_a" or key:"raw_data_b")+ and +(key:"a_b_c_for_sales" or key:"b_c_for_sales")'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select '(key:"raw_data_a" or key:"raw_data_b")+ and +(key:"a_b_c_for_sales" or key:"b_c_for_sales")'
    dagster asset materialize --select '(key:"raw_data_a" or key:"raw_data_b")+ and +(key:"a_b_c_for_sales" or key:"b_c_for_sales")'
    ```
    </TabItem>
</Tabs>

## Select all assets on the path between two sets of assets by tag

```shell
tag:"private"+ and +tag:"public"
```

Selects all assets on the paths between assets tagged with `private` and assets tagged with `public`.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![All assets on the path between two sets of assets by tag](/images/guides/build/assets/asset-selection-syntax/select-assets-between-sets-by-tag.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    private_public_assets_job = define_asset_job(
        name="private_public_assets_job", selection='tag:"private"+ and +tag:"public"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'tag:"private"+ and +tag:"public"'
    dagster asset materialize --select 'tag:"private"+ and +tag:"public"'
    ```
    </TabItem>
</Tabs>

## Select all assets on the path between two groups of assets \{#asset-path}

```shell
group:"sensitive_data"+ and +group:"public_data"
```

Selects all assets on the paths from the `sensitive_data` group to the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![All assets on the path between two groups of assets](/images/guides/build/assets/asset-selection-syntax/select-assets-between-two-groups.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    sensitive_to_public_asset_job = define_asset_job(
        name="sensitive_to_public_asset_job", selection='group:"sensitive_data"+ and +group:"public_data"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'group:"sensitive_data"+ and +group:"public_data"'
    dagster asset materialize --select 'group:"sensitive_data"+ and +group:"public_data"'
    ```
    </TabItem>
</Tabs>

## Select assets between two assets that go through the "middle" asset

```shell
key:"raw_data_c"+ and +key:"combo_a_b_c_data"+ and +key:"summary_stats_1"
```

Selects all assets on the path between the `raw_data_c` asset and `summary_stats_1` asset that go through the `combo_a_b_c_data` asset.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![All assets between two assets that go through a middle asset](/images/guides/build/assets/asset-selection-syntax/select-assets-through-middle-asset.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    middle_asset_job = define_asset_job(
        name="middle_asset_job", selection='key:"raw_data_c"+ and +key:"combo_a_b_c_data"+ and +key:"summary_stats_1"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"raw_data_c"+ and +key:"combo_a_b_c_data"+ and +key:"summary_stats_1"'
    dagster asset materialize --select 'key:"raw_data_c"+ and +key:"combo_a_b_c_data"+ and +key:"summary_stats_1"'
    ```
    </TabItem>
</Tabs>

## Select assets with multiple key components \{#multiple-key-components}

To select an asset with a key containing multiple components, such as a prefix, insert slashes (`/`) between the components:

```shell
key:"my_prefix/raw_data_a"
```

This example selects the `my_prefix/raw_data_a` asset, which is defined below:

```python
@dg.asset(
    key_prefix="my_prefix",
    ...
)
def raw_data_a() -> None:
    ...
```

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Select assets with multiple key components](/images/guides/build/assets/asset-selection-syntax/select-assets-multiple-key-components.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    my_prefix_job = define_asset_job(name="my_prefix_job", selection='key:"my_prefix/raw_data_a"')
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"my_prefix/raw_data_a"'
    dagster asset materialize --select 'key:"my_prefix/raw_data_a"'
    ```
    </TabItem>
</Tabs>

## Select multiple assets with `or` \{#multiple-assets}

To select multiple assets, use the `or` operand. The assets don't have to be dependent on each other. This example selects the `summary_stats_1` and `summary_stats_2` assets:

```shell
key:"summary_stats_1" or key:"summary_stats_2"
```

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Select multiple assets with or](/images/guides/build/assets/asset-selection-syntax/select-multiple-assets-with-or.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    summary_stats_assets_job = define_asset_job(
        name="summary_stats_assets_job", selection='key:"summary_stats_1" or key:"summary_stats_2"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"summary_stats_1" or key:"summary_stats_2"'
    dagster asset materialize --select 'key:"summary_stats_1" or key:"summary_stats_2"'
    ```
    </TabItem>
</Tabs>

## Select downstream assets with a filter \{#filter}

```shell
key:"combo_a_b_c_data"+ and kind:"csv"
```

Selects one layer downstream of `combo_a_b_c_data`, limited to assets of kind `csv`.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Select downstream assets with a filter](/images/guides/build/assets/asset-selection-syntax/select-downstream-assets-with-filter.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    downstream_csv_job = define_asset_job(
        name="downstream_csv_job", selection='key:"combo_a_b_c_data"+ and kind:"csv"'
    )
   ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'key:"combo_a_b_c_data"+ and kind:"csv"'
    dagster asset materialize --select 'key:"combo_a_b_c_data"+ and kind:"csv"'
    ```
    </TabItem>
</Tabs>

## Select assets without a specific tag \{#not-tag}

```shell
owner:"nora.dagster@example.com" and not tag:"customer_data"
```

Selects all assets owned by `nora.dagster@example.com` **excluding** any assets tagged with `customer_data`.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Select assets with a specific owner and without a specific tag](/images/guides/build/assets/asset-selection-syntax/select-assets-owner-not-tag.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    data_eng_not_private_job = define_asset_job(
        name="data_eng_not_private_job", selection='owner:"nora.dagster@example.com" and not tag:"customer_data"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'owner:"nora.dagster@example.com" and not tag:"customer_data"'
    dagster asset materialize --select 'owner:"nora.dagster@example.com" and not tag:"customer_data"'
    ```
    </TabItem>
</Tabs>

## Select assets with parentheses grouping and filters \{#grouping-filters}

### Select a parentheses group `or` assets that belong in a named `group`

```shell
(owner:"team:sales" and kind:"csv") or group:"public_data"
```

Selects assets that are either owned by the sales team and of kind `csv`, **or** that belong to the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Select a parentheses group or assets that belong in a named group](/images/guides/build/assets/asset-selection-syntax/select-parentheses-group-or-named-group.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    sales_csv_public_job = define_asset_job(
        name="sales_csv_public_job", selection='(owner:"team:sales" and kind:"csv") or group:"public_data"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select '(owner:"team:sales" and kind:"csv") or group:"public_data"'
    dagster asset materialize --select '(owner:"team:sales" and kind:"csv") or group:"public_data"'
    ```
    </TabItem>
</Tabs>

### Exclude a parentheses group with `not` and select assets that match a `key` wildcard

```shell
not (kind:"s3" or kind:"csv") and key:"raw*"
```

Selects assets whose keys contain `raw` and are **not** of the kind `s3` or `csv`.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Exclude parentheses group with not and select assets that match a key wildcard](/images/guides/build/assets/asset-selection-syntax/select-assets-not-in-parentheses-group-with-wildcard.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    not_s3_csv_raw_job = define_asset_job(
        name="not_s3_csv_raw_job", selection='not (kind:"s3" or kind:"csv") and key:"raw*"'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'not (kind:"s3" or kind:"csv") and key:"raw*"'
    dagster asset materialize --select 'not (kind:"s3" or kind:"csv") and key:"raw*"'
    ```
    </TabItem>
</Tabs>

## Select roots or sinks

The examples in this section operate on a selection of assets in the `public_data` group:

![Graph of assets in public_data group](/images/guides/build/assets/asset-selection-syntax/select-all-public-data-group.png)

### Select all root assets within an asset selection

```shell
roots(group:"public_data")
```

Selects root assets within the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Roots within public_data group](/images/guides/build/assets/asset-selection-syntax/select-roots-within-public-data-group.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    roots_within_public_data_job = define_asset_job(
        name="roots_within_public_data_job", selection='roots(group:"public_data")'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'roots(group:"public_data")'
    dagster asset materialize --select 'roots(group:"public_data")'
    ```
    </TabItem>
</Tabs>

### Select all sink assets within an asset selection

```shell
sinks(group:"public_data")
```

Selects sink assets within the `public_data` group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Sinks within public_data group](/images/guides/build/assets/asset-selection-syntax/select-sinks-within-public-data-group.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    sinks_within_public_data_job = define_asset_job(
        name="sinks_within_public_data_job", selection='sinks(group:"public_data")'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'sinks(group:"public_data")'
    dagster asset materialize --select 'sinks(group:"public_data")'
    ```
    </TabItem>
</Tabs>

### Select all root assets that feed into an asset selection

```shell
roots(+group:"public_data")
```

Selects root assets that feed into the `public_data` group, but do not belong to that group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Roots that feed to public_data group](/images/guides/build/assets/asset-selection-syntax/select-roots-of-public-data-group.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    roots_feed_to_public_data_job = define_asset_job(
        name="roots_feed_to_public_data_job", selection='roots(+group:"public_data")'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'roots(+group:"public_data")'
    dagster asset materialize --select 'roots(+group:"public_data")'
    ```
    </TabItem>
</Tabs>

### Select all sink assets that depend on assets in a selection

```shell
sinks(group:"public_data"+)
```

Selects sink assets that depend on assets in the `public_data` group, but do not belong to that group.

<Tabs groupId="examples">
    <TabItem value="dagster-ui" label="Dagster UI">
    ![Sinks that depend on public_data group](/images/guides/build/assets/asset-selection-syntax/select-sinks-of-public-data-group.png)
    </TabItem>
    <TabItem value="python" label="Python">
    ```python
    sinks_feed_to_public_data_job = define_asset_job(
        name="sinks_feed_to_public_data_job", selection='sinks(group:"public_data"+)'
    )
    ```
    </TabItem>
    <TabItem value="cli" label="CLI">
    ```shell
    dagster asset list --select 'sinks(group:"public_data"+)'
    dagster asset materialize --select 'sinks(group:"public_data"+)'
    ```
    </TabItem>
</Tabs>
