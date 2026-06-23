---
description: You can define a dependency between two Dagster assets by passing the upstream asset to the deps parameter in the downstream asset's @asset decorator.
sidebar_position: 200
title: Defining assets that depend on other assets
---

Asset definitions can depend on other asset definitions. The dependent asset is called the **downstream asset**, and the asset it depends on is the **upstream asset**.

import ScaffoldAsset from '@site/docs/partials/\_ScaffoldAsset.md';

<ScaffoldAsset />

## Defining basic dependencies

You can define a dependency between two assets by passing the upstream asset to the `deps` parameter in the downstream asset's `@asset` decorator.

In this example, the asset `sugary_cereals` creates a new table (`sugary_cereals`) by selecting records from the `cereals` table. Then the asset `shopping_list` creates a new table (`shopping_list`) by selecting records from `sugary_cereals`:

<CodeExample
    path="docs_snippets/docs_snippets/guides/build/assets/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_basic_dependencies"
    endBefore="end_basic_dependencies"
    title="src/<project_name>/defs/assets.py"
/>

## Defining asset dependencies across code locations

:::info

Assets in different code locations cannot be materialized in the same run. To trigger a downstream asset in another code location after an upstream asset materializes, use a [sensor](/guides/automate/sensors) or [declarative automation](/guides/automate/declarative-automation).

:::

Assets can depend on assets in different [code locations](/guides/build/projects).

:::note

Declaring a dependency with `deps` only tracks lineage across code locations. To pass the upstream asset's data to the downstream asset as an input, see [Using data from another code location as an input](#using-data-from-another-code-location-as-an-input).

:::

In the following example, the `code_location_1_asset` asset produces a JSON string from a file in `code_location_1`:

<CodeExample
    path="docs_snippets/docs_snippets/guides/build/assets/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_code_location_one_asset_decorator"
    endBefore="end_code_location_one_asset_decorator"
    title="src/<project_name>/defs/assets.py"
/>

In `code_location_2`, we can reference `code_location_1_asset` it via its asset key:

<CodeExample
    path="docs_snippets/docs_snippets/guides/build/assets/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_code_location_two_asset_decorator"
    endBefore="end_code_location_two_asset_decorator"
    title="src/<project_name>/defs/assets.py"
/>

### Using data from another code location as an input

Declaring a dependency with `deps` tracks lineage across code locations, but does not pass the upstream asset's data to the downstream asset as an input.

To use data from an asset in another code location as an input to a downstream asset, declare the upstream asset as an `AssetSpec` in your code location with an I/O manager key. Include the `AssetSpec` in your `Definitions` object alongside your downstream asset.

:::note

`SourceAsset` was the previous way to do this and is now deprecated. Use `AssetSpec(...).with_io_manager_key(...)` instead.

:::

In the example below, `daily_sales_data` is defined in another code location and used as an input to `enriched_sales_data`:

<CodeExample
    path="docs_snippets/docs_snippets/guides/build/assets/cross_code_location_dependencies.py"
    language="python"
    startAfter="start_scenario_b"
    endBefore="end_scenario_b"
    title="src/<project_name>/defs/assets.py"
/>

Cross-code-location dependencies on partitioned assets work the same way. For more information, see [Partitioning assets](/guides/build/partitions-and-backfills/partitioning-assets).
