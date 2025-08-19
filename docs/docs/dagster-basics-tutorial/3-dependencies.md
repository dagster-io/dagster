---
title: Dependencies
description: Defining dependencies between assets
sidebar_position: 40
---

Right now, we have several assets that are independent of each other. In most data platforms, assets are connected to form a DAG.

We will add another asset to our `Definitions` and link it to the assets we had previously defined.

<p align="center">
  <img src="/images/tutorial/dagster-tutorial/overviews/dependencies.png" alt="2048 resolution" width="75%" />
</p>

## 1. Create a downstream asset

Creating a downstream asset is the same as creating any other asset. Here, we will define a table that relies on the data from all of the assets we have already created.

To link the assets together, set the `deps` parameter within the asset decorator. Dagster uses this information to build the asset graph:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/assets.py"
  language="python"
  startAfter="start_define_assets_with_dependencies"
  endBefore="end_define_assets_with_dependencies"
  title="src/dagster_tutorial/defs/assets.py"
/>

## 2. Materialize the assets

To view the updated asset graph, navigate to [http://127.0.0.1:3000](http://127.0.0.1:3000) (or restart `dg dev` if it has been closed) and reload the definitions:

1. Navigate to **Assets**.
2. Click **Reload definitions**.

   ![2048 resolution](/images/tutorial/dagster-tutorial/dependency-1.png)

## 3. Asset selection

In Dagster, [asset selection](/guides/build/assets/asset-selection-syntax) syntax provides a powerful and flexible way to specify exactly which assets to materialize, observe, or run in a job. You can select assets explicitly by their key (for example, `customers`) or use wildcard patterns and hierarchical paths to target groups of related assets.

:::tip

To select all assets downstream of `customers`, use `key:"customers"+`. You can also chain selectors with logical operators to combine multiple sets.

![2048 resolution](/images/tutorial/dagster-tutorial/dependency-2.png)

:::
