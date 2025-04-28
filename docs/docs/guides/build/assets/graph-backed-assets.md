---
title: Graph-backed assets
description: An asset definition with multiple discrete computations combined in an op graph.
position: 1400
---

Basic assets are computed using a single op. If generating an asset involves multiple discrete computations, you can use graph-backed assets by separating each computation into an op and assembling them into an op graph to combine your computations. This allows you to launch re-executions of runs at the op boundaries, but doesn't require you to link each intermediate value to an asset in persistent storage.

## Relevant APIs

| Name                                                       | Description                                                                                                                                                              |
| ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| <PyObject section="assets" module="dagster" object="graph_asset" decorator />                | Decorator for defining an asset that's computed using a graph of ops. The dependencies between the ops are specified inside the body of the decorated function.          |
| <PyObject section="assets" module="dagster" object="graph_multi_asset" decorator />          | Decorator for defining a set of assets that are computed using a graph of ops. The dependencies between the ops are specified inside the body of the decorated function. |
| <PyObject section="assets" module="dagster" object="AssetsDefinition.from_graph" /> | Constructs an asset, given a graph definition. Useful if you have a single graph that you want to use to power multiple different assets.                                |

## Defining graph-backed assets

To define a graph-backed asset, use the <PyObject section="assets" module="dagster" object="graph_asset" decorator /> decorator. The decorated function defines the dependencies between a set of ops, which are combined to compute the asset.

In the example below, when you tell Dagster to materialize the `slack_files_table` asset, Dagster will invoke `fetch_files_from_slack` and then invoke `store_files` after `fetch_files_from_slack` has completed:

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/graph_backed_asset.py" startAfter="start example" endBefore="end example" />

### Defining managed-loading dependencies for graph-backed assets

Similar to single-op asset definitions, Dagster infers the upstream assets from the names of the arguments to the decorated function. Dagster will then delegate loading the data to an [I/O manager](/guides/build/io-managers).

The example below includes an asset named `middle_asset`. `middle_asset` depends on `upstream_asset`, and `downstream_asset` depends on `middle_asset`:

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/graph_backed_asset.py" startAfter="start_basic_dependencies" endBefore="end_basic_dependencies" />

### Graph-backed multi-assets

Using the <PyObject section="assets" module="dagster" object="graph_multi_asset" decorator />, you can create a combined definition of multiple assets that are computed using the same graph of ops and same upstream assets.

In the below example, `two_assets` accepts `upstream_asset` and outputs two assets, `first_asset` and `second_asset`:

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/graph_backed_asset.py" startAfter="start_basic_dependencies_2" endBefore="end_basic_dependencies_2" />

### Advanced: Subsetting graph-backed assets

By default, when executing a graph-backed asset, every asset produced by the graph must be materialized. This means that attempting to selectively execute a subset of assets defined in the graph-backed asset will result in an error.

If the underlying computation is sufficiently flexible to selectively output a subset of assets, a graph-backed asset can be subsetted. For example, let’s say we wanted to define a graph-backed asset with the structure depicted in the image below. In this case, we want to independently materialize `foo_asset` and `baz_asset`.

![Graph-backed asset](/images/guides/build/assets/graph-backed-asset.png)

In order to selectively output an asset from a graph-backed asset, Dagster will run each op that is a dependency of the outputted asset. In the example, if we wanted to selectively materialize `foo_asset`, Dagster would run `foo` and `bar`. If we wanted to selectively materialize `baz_asset`, Dagster would run all three ops (`foo`, `bar`, and `baz`).

Because the `foo` op yields an asset output (`foo_asset`) and is an upstream dependency of another asset generated from the graph (`baz_asset`), we need to structure `foo` to selectively return outputs depending on the asset subset selected for execution. We can do this by defining `foo` to have optional outputs that are yielded conditionally. Dagster provides a `context.selected_output_names` object on the op context that will return the outputs necessary to generate the asset subset.

During execution, if we select just `baz_asset` for materialization, the below implementation of `foo` will return `{"foo_2"}` for `context.selected_output_names`, preventing `foo_asset` from being materialized.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/subset_graph_backed_asset.py" startAfter="start_graph_backed_asset_foo" endBefore="end_graph_backed_asset_foo" />

Because Dagster flattens each op graph into a flat input/output mapping between ops under the hood, any op that produces an output of the graph must be structured to yield its outputs optionally, enabling the outputs to be returned independently.

In the example, `foo` and `baz` produce outputs of `my_graph`. Subsequently, their outputs need to be yielded optionally. Because `foo` yields multiple outputs, we must structure our code to conditionally yield its outputs like in the code snippet above.

However, because `baz` only yields a singular output, Dagster will only run `baz` when its asset output `baz_asset` is selected. So, we don’t have to structure `baz` to return an optional output. Because `bar` does not yield any outputs that are returned from `my_graph`, its outputs do not have to be selectively returned.

We could define the asset using the code below. Notice that `can_subset` must be set to `True` in the asset definition to signify that the graph-backed asset can be subsetted.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/subset_graph_backed_asset.py" startAfter="start_graph_backed_asset_example" endBefore="end_graph_backed_asset_example" />

Depending on how outputs are returned from the ops within a graph-backed asset, there could be unexpected materializations. For example, the following `foo` implementation would unexpectedly materialize `foo_asset` if `baz_asset` was the only asset selected for execution.

<CodeExample path="docs_snippets/docs_snippets/concepts/assets/subset_graph_backed_asset_unexpected_materializations.py" startAfter="start_unexpected_materialization_foo" endBefore="end_unexpected_materialization_foo" />

This is because the `foo` op is an upstream dependency of `baz_asset`, and this implementation of `foo` returns both the `foo_1` and `foo_2` outputs. The `foo_1` output is returned as the `foo_asset` output of the graph, causing an unexpected materialization of `foo_asset`.
