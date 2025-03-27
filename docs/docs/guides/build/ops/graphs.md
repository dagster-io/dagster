---
title: "Op graphs"
description: Op graphs are sets of interconnected ops or sub-graphs and form the core of jobs.
sidebar_position: 400
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

A graph is a set of interconnected [ops](/guides/build/ops/) or sub-graphs. While individual ops typically perform simple tasks, ops can be assembled into a graph to accomplish complex tasks.

Graphs can be used in three different ways:

- [**To back assets**](/guides/build/assets/defining-assets#graph-asset) - Basic assets are computed using a single op, but if computing one of your assets requires multiple discrete steps, you can compute it using a graph instead.
- [**Directly inside a job**](/guides/build/jobs/op-jobs) - Each op job contains a graph.
- [**Inside other graphs**](/guides/build/ops/nesting-graphs) - You can build complex graphs out of simpler graphs.

## Relevant APIs

| Name                                                   | Description                                                                                                                                                                                                                       |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="graphs" module="dagster" object="graph" decorator /> | The decorator used to define an op graph, which can form the basis for multiple jobs. |
| <PyObject section="graphs" module="dagster" object="GraphDefinition" /> | An op graph definition, which is a set of ops (or [sub-graphs](/guides/build/ops/nesting-graphs)) wired together. Forms the core of a job. Typically constructed using the <PyObject section="jobs" module="dagster" object="job" decorator /> decorator. |

## Creating op graphs

- [Using the @graph decorator](#using-the-graph-decorator)
- [Graph patterns](#op-graph-patterns)

### Using the `@graph` decorator

To create an op graph, use the <PyObject section="graphs" module="dagster" object="graph" decorator /> decorator.

In the following example, we return one output from the root op (`return_one`) and pass data along through single inputs and outputs:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/linear_graph.py" startAfter="start_marker" endBefore="end_marker" />

### Op graph patterns

Need some inspiration? Using the patterns below, you can build op graphs:

- [Reuse an op definition](#reuse-an-op-definition)
- [With multiple inputs](#with-multiple-inputs)
- [With conditional branching](#with-conditional-branching)
- [With a fixed fan-in](#with-a-fixed-fan-in)
- [That contain other op graphs](#that-contain-other-op-graphs)
- [That use dynamic outputs](#using-dynamic-outputs)

#### Reuse an op definition

You can use the same op definition multiple times in the same graph. Note that this approach can also apply to [op jobs](/guides/build/jobs/op-jobs).

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/graphs.py" startAfter="start_multiple_usage_graph" endBefore="end_multiple_usage_graph" />

To differentiate between the two invocations of `add_one`, Dagster automatically aliases the op names to be `add_one` and `add_one_2`.

You can also manually define the alias by using the `.alias` method on the op invocation:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/graphs.py" startAfter="start_alias_graph" endBefore="end_alias_graph" />

#### With multiple inputs

![Multiple inputs](/images/guides/build/ops/multi-inputs.png)

A single output can be passed to multiple inputs on downstream ops. In this example, the output from the first op is passed to two different ops. The outputs of those ops are combined and passed to the final op:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/multiple_io_graph.py" startAfter="start_marker" endBefore="end_marker" />

#### With conditional branching

![Conditional branch](/images/guides/build/ops/conditional.png)

As an op only starts to execute once all its inputs have been resolved, you can use this behavior to model conditional execution.

In this example, the `branching_op` outputs either the `branch_1` result or `branch_2` result. Since op execution is skipped for ops that have unresolved inputs, only one of the downstream ops will execute:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/branching_graph.py" startAfter="start_marker" endBefore="end_marker" />

:::note

When using conditional branching, <PyObject section="ops" module="dagster" object="Output" /> objects must be yielded instead of returned.

:::

#### With a fixed fan-in

![Fixed fan-in](/images/guides/build/ops/fixed-fan-in.png)

If you have a fixed set of ops that all return the same output type, you can collect the outputs into a list and pass them into a single downstream op.

The downstream op executes only if all of the outputs were successfully created by the upstream op:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/fan_in_graph.py" startAfter="start_marker" endBefore="end_marker" />

In this example, we have 10 ops that all output the number `1`. The `sum_fan_in` op takes all of these outputs as a list and sums them.

#### That contain other op graphs

Op graphs can contain other op graphs. Refer to the [Nesting op graphs documentation](/guides/build/ops/nesting-graphs) for more info and examples.

#### Using dynamic outputs

Using dynamic outputs, you can duplicate portions of an op graph at runtime. Refer to the [Dynamic graphs documentation](/guides/build/ops/dynamic-graphs) for more info and examples.

## Defining and constructing dependencies

- [Defining nothing dependencies](#defining-nothing-dependencies)
- [Loading an asset as an input](#loading-an-asset-as-an-input)
- [Constructing dependencies](#constructing-dependencies)

### Defining nothing dependencies

Dependencies in Dagster are primarily _data dependencies_. Using data dependencies means each input of an op depends on the output of an upstream op.

If you have an op, say `Op A`, that does not depend on any outputs of another op, say `Op B`, there theoretically shouldn't be a reason for `Op A` to run after `Op B`. In most cases, these two ops should be parallelizable. However, there are some cases where an explicit ordering is required, but it doesn't make sense to pass data through inputs and outputs to model the dependency.

If you need to model an explicit ordering dependency, you can use the <PyObject section="types" module="dagster" object="Nothing"/> Dagster type on the input definition of the downstream op. This type specifies that you are passing "nothing" via Dagster between the ops, while still using inputs and outputs to model the dependency between the two ops.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graphs/order_based_dependency.py" startAfter="start_marker" endBefore="end_marker" />

In this example, `create_table_2` has an input of type `Nothing` meaning that it doesn't expect any data to be provided by the upstream op. This lets us connect them in the graph definition so that `create_table_2` executes only after `create_table_1` successfully executes.

`Nothing` type inputs do not have a corresponding parameter in the function since there is no data to pass. When connecting the dependencies, it is recommended to use keyword args to prevent mix-ups with other positional inputs.

Note that in most cases, it is usually possible to pass some data dependency. In the example above, even though we probably don't want to pass the table data itself between the ops, we could pass table pointers. For example, `create_table_1` could return a `table_pointer` output of type `str` with a value of `table_1`, and this table name can be used in `create_table_2` to more accurately model the data dependency.

Dagster also provides more advanced abstractions to handle dependencies and IO. If you find that you are finding it difficult to model data dependencies when using external storage, check out [IO managers](/guides/build/io-managers/).

### Loading an asset as an input

You can supply an asset as an input to one of the ops in a graph. Dagster can then use the [I/O manager](/guides/build/io-managers/) on the asset to load the input value for the op.

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/assets_ops_graphs/op_graph_asset_input.py" />

We must use the <PyObject section="assets" module="dagster" object="AssetsDefinition.get_asset_spec" />, because <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> are used to represent assets that other assets or jobs depend on, in settings where they won't be materialized themselves.

If the asset is partitioned, then:

- If the job is partitioned, the corresponding partition of the asset will be loaded.
- If the job is not partitioned, then all partitions of the asset will be loaded. The type that they will be loaded into depends on the I/O manager implementation.

### Constructing dependencies

- [Using GraphDefinitions](#using-graphdefinitions)
- [Using YAML (GraphDSL)](#using-yaml-graphdsl)

#### Using `GraphDefinitions`

You may run into a situation where you need to programmatically construct the dependencies for a graph. In that case, you can directly define the <PyObject section="graphs" module="dagster" object="GraphDefinition"/> object.

To construct a GraphDefinition, you need to pass the constructor a graph name, a list of op or graph definitions, and a dictionary defining the dependency structure. The dependency structure declares the dependencies of each op’s inputs on the outputs of other ops in the graph. The top-level keys of the dependency dictionary are the string names of ops or graphs. If you are using op aliases, be sure to use the aliased name. Values of the top-level keys are also dictionary, which maps input names to a <PyObject section="graphs" module="dagster" object="DependencyDefinition"/>.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/jobs.py" startAfter="start_pipeline_definition_marker" endBefore="end_pipeline_definition_marker" />

#### Using YAML (GraphDSL)

Sometimes you may want to construct the dependencies of an op graph definition from a YAML file or similar. This is useful when migrating to Dagster from other workflow systems.

For example, you can have a YAML like this:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/my_graph.yaml" />

You can programmatically generate a GraphDefinition from this YAML:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dep_dsl.py" startAfter="start" />

## Using graphs

- [Inside assets](#inside-assets)
- [Directly inside op jobs](#directly-inside-op-jobs)

### Inside assets

Op graphs can be used to create [asset definitions](/guides/build/assets/). Graph-backed assets are useful if you have an existing op graph that produces and consumes assets.

Wrapping your graph inside an asset definition gives you all the benefits of software-defined assets — like cross-job lineage — without requiring you to change the code inside your graph. Refer to the [graph-backed assets documentation](/guides/build/assets/defining-assets#graph-asset) for more info and examples.

### Directly inside op jobs

Ready to start using your op graphs in Dagster op jobs? Refer to the [Op jobs documentation](/guides/build/jobs/op-jobs) for detailed info and examples.
