---
title: "Create data assets"
sidebar_position: 10
---

Data assets are at the core of Dagster. By modelling your data as assets you unlock: declarative automation, lineage, and a searchable data catalog. This guide will help you understand how to model your data as assets.

There are three ways of create data assets:

* Using the `@asset` decorator to declare a single asset.
* Using the `@multi_asset` decorator to output multiple assets from a single operation.
* Using the `@graph_asset` decorator to output a single asset from multiple operations without making each operation itself an asset.

This guide walks through all three methods.

***

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

* A basic understanding of Dagster concepts such as assets and resources
* Dagster installed and a working project setup

</details>

***

## Define a single data asset using the `@asset` decorator

The simplest way to define a data asset in Dagster is by using the `@asset` decorator. This decorator marks a Python function as an asset, with the function's output being the data produced by the asset.

```python
@asset
def my_data_asset():
    return {"key": "value"}
```

In this example, `my_data_asset` is an asset that returns a simple dictionary. Dagster automatically tracks the dependencies of this asset and handles its execution within the pipeline.

The benefits of this approach are:

* The asset is self-contained, which makes the code easier to test and maintain.

The downsides of this approach are:

* It’s not well-suited for cases where multiple related assets need to be produced from a single operation.

## Define multiple data assets using the `@multi_asset` decorator

When you need to generate multiple assets from a single operation, you can use the `@multi_asset` decorator. This allows you to output multiple assets while maintaining a single processing function.

```python
@multi_asset(
    outs={
        "asset_one": AssetOut(),
        "asset_two": AssetOut()
    }
)
def my_multi_asset():
    return {"asset_one": "value1", "asset_two": "value2"}
```

In this example, `my_multi_asset` produces two assets: `asset_one` and `asset_two`. Each is derived from the same function, which makes it easier to handle related data transformations together.

The benefits of this approach are:

* It's efficient in scenarios where a single operation naturally produces multiple outputs, such as a batched API call that returns multiple tables

The downsides of this approach are:

* (TODO: Validate if this is correct?, eg could we yield some assets while the tail assets fail?)  Either all assets fail or pass together

## Define a single asset from multiple operations using the `@graph_asset` decorator

For cases where you need to perform multiple operations to produce a single asset, you can use the `@graph_asset` decorator. This allows you to encapsulate a series of operations and expose them as a single asset.

```python3
@graph_asset
def complex_asset():
    @op
    def step_one():
        return "intermediate_value"

    @op
    def step_two(value):
        return f"final_{value}"

    return step_two(step_one())
```

In this example, `complex_asset` is an asset that is the result of two operations: `step_one` and `step_two`. These steps are combined into a single asset, abstracting away the intermediate computations.

The benefits of this approach are:

* It enables you to model complex data processing pipelines while exposing only the final output as an asset.
* It keeps the asset lineage graph clean, with all internal complexity hidden within the graph.
* (TODO: Is this accurate?) Individual ops can be retried using retry policies automatically or from the Dagster UI.

The downsides of this approach are:

* (TODO: Is this accurate?) Since the individual ops are not assets there is no historical record of their evaluations

***

## Related resources

TODO: add links to relevant API documentation here.
Link to @asset api
Link to @multi\_asset api.
Link to @graph\_asset api.
