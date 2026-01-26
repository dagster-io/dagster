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
    path="docs_snippets/docs_snippets/guides/data-modeling/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_basic_dependencies"
    endBefore="end_basic_dependencies"
    title="src/<project_name>/defs/assets.py"
/>

## Defining asset dependencies across code locations

Assets can depend on assets in different [code locations](/guides/build/projects). In the following example, the `code_location_1_asset` asset produces a JSON string from a file in `code_location_1`:

<CodeExample
    path="docs_snippets/docs_snippets/guides/data-modeling/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_code_location_one_asset_decorator"
    endBefore="end_code_location_one_asset_decorator"
    title="src/<project_name>/defs/assets.py"
/>

In `code_location_2`, we can reference `code_location_1_asset` by its asset key:

<CodeExample
    path="docs_snippets/docs_snippets/guides/data-modeling/asset-dependencies/asset-dependencies.py"
    language="python"
    startAfter="start_code_location_two_asset_decorator"
    endBefore="end_code_location_two_asset_decorator"
    title="src/<project_name>/defs/assets.py"
/>

