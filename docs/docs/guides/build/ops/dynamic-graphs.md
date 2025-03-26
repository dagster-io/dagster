---
title: "Dynamic graphs"
description: Dagster APIs for runtime determined graph structures.
sidebar_position: 600
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

The ability for portions of a [graph](/guides/build/ops/graphs) to be duplicated at runtime.

## Relevant APIs

| Name                                                 | Description                                                                                   |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| <PyObject section="dynamic" module="dagster" object="DynamicOut" />    | Declare that an op will return dynamic outputs                                                |
| <PyObject section="dynamic" module="dagster" object="DynamicOutput" /> | The object that an op will yield repeatedly, each containing a value and a unique mapping_key |

## Overview

The basic unit of computation in Dagster is the [op](/guides/build/ops/). In certain cases it is desirable to run the same op multiple times on different pieces of similar data.

Dynamic outputs are the tool Dagster provides to allow resolving the pieces of data at runtime and having downstream copies of the ops created for each piece.

## Using dynamic outputs

### A static job

Here we start with a contrived example of a job containing a single expensive op:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="non_dyn_start" endBefore="non_dyn_end" />

While, the implementation of `expensive_processing` can internally do something to parallelize the compute, if anything goes wrong with any part we have to restart the whole computation.

### A dynamic job

With this motivation we will break up the computation using Dynamic Outputs. First we will define our new op that will use dynamic outputs. First we use <PyObject section="dynamic" module="dagster" object="DynamicOut" /> to declare that this op will return dynamic outputs. Then in the function we `yield` a number of <PyObject section="dynamic" module="dagster" object="DynamicOutput" /> objects that each contain a value and a unique `mapping_key`.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_out_start" endBefore="dyn_out_end" />

Then after creating ops for our downstream operations, we can put them all together in a job.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_job_start" endBefore="dyn_job_end" />

Within our `@job` decorated composition function, the object representing the dynamic output can not be passed directly to another op. Either `map` or `collect` must be invoked on it.

`map` takes a `Callable` which receives a single argument. This callable is evaluated once, and any invoked op that is passed the input argument will establish dependencies. The ops downstream of a dynamic output will be cloned for each dynamic output, and identified using the associated `mapping_key`. The return value from the callable is captured and wrapped in an object that allows for subsequent `map` or `collect` calls.

`collect` creates a fan-in dependency over all the dynamic copies. The dependent op will receive a list containing all the values.

## Advanced mapping examples

### Returning dynamic outputs

In addition to yielding, <PyObject section="dynamic" module="dagster" object="DynamicOutput" /> objects can also be returned as part of a list.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_out_return_start" endBefore="dyn_out_return_end" />

<PyObject section="dynamic" module="dagster" object="DynamicOutput" /> can be used as a generic type annotation describing the expected type of the output.

### Chaining

The following two examples are equivalent ways to establish a sequence of ops that occur for each dynamic output.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_chain_start" endBefore="dyn_chain_end" />

### Additional arguments

A lambda or scoped function can be used to pass non-dynamic outputs along side dynamic ones in `map` downstream.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_add_start" endBefore="dyn_add_end" />

### Multiple outputs

Multiple outputs are returned via a `namedtuple`, where each entry can be used via `map` or `collect`.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/dynamic.py" startAfter="dyn_mult_start" endBefore="dyn_mult_end" />
