---
title: "Create data assets"
sidebar_position: 10
---

Data assets are at the core of Dagster. By modeling your data as assets, you unlock: Declarative Automation, lineage, and a searchable data catalog. This guide will help you understand how to model your data as assets.

There are four ways to create data assets:

* Using the `@asset` decorator to declare a single asset.
* Using the `@multi_asset` decorator to output multiple assets from a single operation.
* Using the `@graph_asset` decorator to output a single asset from multiple operations without making each operation itself an asset.
* Using the `@graph_multi_asset` decorator to output multiple assets from multiple operations

This guide walks you the first three methods. The fourth combines the approaches of the 2nd and 3rd so it's omitted.

***

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

* Dagster installed and a working project setup

</details>

***

## Define a single data asset using the `@asset` decorator

The simplest way to define a data asset in Dagster is by using the `@asset` decorator. This decorator marks a Python function as an asset, with the function's output being the data produced by the asset.

<CodeExample filePath="guides/data-assets/data-assets/asset_docorator.py" language="python" title="Using @dg.asset decorator" />

In this example, my\_data\_asset is an asset that logs its output. Dagster automatically tracks its dependencies and handles its execution within the pipeline.

## Define multiple data assets using the `@multi_asset` decorator

When you need to generate multiple assets from a single operation, you can use the `@multi_asset` decorator. This allows you to output multiple assets while maintaining a single processing function.

<CodeExample filePath="guides/data-assets/data-assets/multi_asset_docorator.py" language="python" title="Using @dg.multi_asset decorator" />

In this example, `my_multi_asset` produces two assets: `asset_one` and `asset_two`. Each is derived from the same function, which makes it easier to handle related data transformations together.

Multi-assets may be useful in the following scenarios:

* A single call to an API results in multiple tables being updated.
* The same in-memory object is used to compute multiple assets.

The downsides of this approach are:

* By default, all assets defined in a multi-asset must be materialized together, although this can be mitigated by setting the can\_subset parameter to True.
* Assets are tightly coupled so one asset failing can cause other assets to fail.

## Define a single asset from multiple operations using the `@graph_asset` decorator

For cases where you need to perform multiple operations to produce a single asset, you can use the `@graph_asset` decorator. This allows you to encapsulate a series of operations and expose them as a single asset.

<CodeExample filePath="guides/data-assets/data-assets/graph_asset_docorator.py" language="python" title="Using @dg.graph_asset decorator" />

In this example, `complex_asset` is an asset that's the result of two operations: `step_one` and `step_two`. These steps are combined into a single asset, abstracting away the intermediate representations.

The benefits of this approach are:

* It enables you to model complex data processing pipelines while exposing only the final output as an asset.
* It keeps the asset lineage graph clean, with all internal complexity hidden within the graph.
* Individual ops can be reused across different assets or graphs, promoting code reuse.
* Individual ops can be retried automatically by setting a RetryPolicy or manually from the Dagster UI.

***

## Related resources

<!-- TODO: add links to relevant API documentation here.
Link to @asset api
Link to @multi\_asset api.
Link to @graph\_asset api.
Link to @grpah\_multi\_asset api. -->
