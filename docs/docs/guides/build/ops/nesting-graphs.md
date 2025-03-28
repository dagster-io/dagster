---
title: 'Nesting op graphs'
description: To organize the ops inside a job, you can nest sets of ops into sub-graphs.
sidebar_position: 500
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

To organize the [ops](/guides/build/ops/) inside a [job](/guides/build/jobs/op-jobs), you can nest sets of ops into sub-graphs.

## Relevant APIs

| Name                                                   | Description                           |
| ------------------------------------------------------ | ------------------------------------- |
| <PyObject section="graphs" module="dagster" object="graph" decorator /> | The decorator used to define a graph. |

## Overview

A Dagster job is usually based on a graph of connected ops, but its graph can also contain other graphs. Nesting graphs is useful for organizing large or complicated graphs and for abstracting away complexity. Dagster supports arbitrary levels of nesting.

We use the term _node_ to refer to both ops and graphs, because both ops and graphs can be used as nodes inside graphs.

## Nesting graphs inside graphs

### A job without nesting

As a baseline, here's a job that does not use nesting. It starts with an op that returns a number, then uses two ops to convert it from Celsius to Fahrenheight, then logs the result:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/unnested_ops.py" />

### Nesting

We can put the ops that perform the Celsius-to-Fahrenheit conversion into their own sub-graph and invoke that sub-graph from our job's main graph:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/nested_graphs.py" startAfter="start_composite_solid_example_marker" endBefore="end_composite_solid_example_marker" />

When executed, the above example will do the exact same thing as the non-nested version, but the nesting allows better organization of code and simplifies the presentation of the main graph in the Dagster UI.

## Sub-graph inputs and outputs

As shown in the example above, sub-graphs can have inputs and outputs - `celsius_to_fahrenheit` accepts a `number` argument, and it has a return statement. Sub-graph inputs and outputs enable connecting the inputs and outputs of nodes inside the graph to the inputs and outputs of nodes outside the graph. In the `all_together_nested` example:

- The `number` input of the `celsius_to_fahrenheit` graph is passed as an argument to the `multiply_by_one_point_eight` op. This means that, when an outer graph invokes `celsius_to_fahrenheit` and provides the output of another op or sub-graph for the `number` arg, the output of that op or sub-graph will be passed to `multiply_by_one_point_eight`, and `multiply_by_one_point_eight` will not execute until the upstream op that produces the output has completed.
- The implementation of the `celsius_to_fahrenheit` graph returns the result of the `add_thirty_two` op. This means that, when an outer graph invokes `celsius_to_fahrenheit` and passes its output to the input of another node, the output of `add_thirty_two` will be provided to that node, and any ops that ultimately receive that input will not execute until `add_thirty_two` has completed.

If you want to add a description to an input (that will display in the UI), you can provide a <PyObject section="graphs" module="dagster" object="GraphIn" /> when constructing the graph.

### Sub-graph configuration

To provide configuration to ops inside a sub-graph when launching a run, you provide config for them under a key with the name of that sub-graph.

This example two ops that both take config and are wrapped by a graph, which is included inside a job.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/nested_graphs.py" startAfter="start_composite_solid_config_marker" endBefore="end_composite_solid_config_marker" />

To kick off a run of this job, you will need to specify the config for both `add_n` and `multiply_by_m` through the sub-graph:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/composite_config.yaml" />

### Configuration mapping

Sub-graphs can dictate config for the ops and sub-graphs inside them. If the full config is known at the time that you're defining the graph, you can pass a dictionary to the `config` argument of the <PyObject section="graphs" module="dagster" object="graph" decorator /> decorator.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graph_provides_config.py" />

Alternatively, you can use "config mapping", i.e. you can provide a function that accepts config that's provided to the graph and generates config for the nodes inside the graph.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/graph_provides_config_mapping.py" />

To run a job that contains `to_fahrenheit` as a sub-graph, you need to provide a value for the `from_unit` config option:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/composite_config_mapping.yaml" />

## Examples

### Multiple outputs

To have multiple outputs from a graph, you need to define the outputs it maps and return a dictionary, where the keys are the output names and the values are the output values.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/nested_graphs.py" startAfter="start_composite_multi_output_marker" endBefore="end_composite_multi_output_marker" />
