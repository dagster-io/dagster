---
title: 'Ops'
description: Ops are the core unit of computation in Dagster and contain the logic of your orchestration graph.
sidebar_position: 80
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

Ops are the core unit of computation in Dagster.

An individual op should perform relatively simple tasks, such as:

- Deriving a dataset from other datasets
- Executing a database query
- Initiating a Spark job in a remote cluster
- Querying an API and storing the result in a data warehouse
- Sending an email or Slack message

The computational core of an [asset definition](/guides/build/assets/) is an op. Collections of ops can also be assembled to create a [graph](/guides/build/ops/graphs).

![Ops](/images/guides/build/ops/ops.png)

Ops support a variety of useful features for data orchestration, such as:

- **Flexible execution strategies**: Painlessly transition from development to production with ops, as they are sealed units of logic independent of execution strategy. Collections of ops - called [graphs](/guides/build/ops/graphs) - can be bound via [jobs](/guides/build/jobs/) to an appropriate [executor](/guides/operate/run-executors) for single-process execution or distribution across a cluster.

- **Pluggable external systems**: If your data pipeline interfaces with external systems, you may want to use local substitutes during development over a cloud-based production system. Dagster provides [resources](/guides/build/external-resources/) as an abstraction layer for this purpose.

  Ops can be written against abstract resources (e.g. `database`), with resource definitions later bound at the [job](/guides/build/jobs/op-jobs) level. Op logic can thus remain uncoupled to any particular implementation of an external system.

- **Input and output management**: Ops have defined [inputs and outputs](#inputs-and-outputs), analogous to the arguments and return value(s) of a Python function. An input or output can be annotated with a [Dagster type](/api/python-api/types) for arbitrarily complex runtime validation. Outputs can additionally be tagged with an [IO Manager](/guides/build/io-managers/) to manage storage of the associated data in between ops. This enables easy swapping of I/O strategy depending on the execution environment, as well as efficient caching of data intermediates.

- **Configuration**: Operations in a data pipeline are often parameterized by both upstream data (e.g. a stream of database records) and configuration parameters independent of upstream data (e.g. a "chunk size" of incoming records to operate on). Define configuration parameters by providing an associated [config schema](/guides/operate/configuration/run-configuration) to the op.

- **Event streams**: Ops emit a stream of [events](/guides/build/ops/op-events) during execution. Certain events are emitted by default - such as indicating the start of an op's execution - but op authors are additionally given access to an event API.

  This can be used to report data asset creation or modification (<PyObject section="ops" module="dagster" object="AssetMaterialization"/>), the result of a data quality check (<PyObject section="ops" module="dagster" object="ExpectationResult"/>), or other arbitrary information. Event streams can be visualized in [the Dagster UI](/guides/operate/webserver#dagster-ui-reference). This rich log of execution facilitates debugging, inspection, and real-time monitoring of running jobs.

- **Testability**: The properties that enable flexible execution of ops also facilitate versatile testing. Ops can be [tested](/guides/test/) in isolation or as part of a pipeline. Further, the [resource](/guides/build/external-resources/) API allows external systems (e.g. databases) to be stubbed or substituted as needed.

## Relevant APIs

| Name                                    | Description                                                                                                                                                                      |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| <PyObject section="ops" module="dagster" object="op" object="op" decorator />      | A decorator used to define ops. Returns an <PyObject section="ops" module="dagster" object="OpDefinition" />. The decorated function is called the "compute function". |
| <PyObject section="ops" module="dagster" object="In" />                | An input to an op. Defined on the `ins` argument to the <PyObject section="ops" module="dagster" object="op" object="op" decorator/> decorator. |
| <PyObject section="ops" module="dagster" object="Out" />               | An output of an op. Defined on the `out` argument to the <PyObject section="ops" module="dagster" object="op" object="op" displayText="op" decorator /> decorator. |
| <PyObject section="execution" module="dagster" object="OpExecutionContext" /> | An object exposing Dagster system APIs for resource access, logging, and more. Can be injected into an op by specifying `context` as the first argument of the compute function. |
| <PyObject section="ops" module="dagster" object="OpDefinition" />     | Class for ops. You will rarely want to instantiate this class directly. Instead, you should use the <PyObject section="ops" module="dagster" object="op" object="op" decorator />. |

## Defining an op

To define an op, use the <PyObject section="ops" module="dagster" object="op" object="op" decorator /> decorator. The decorated function is called the `compute_fn`.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_op_marker" endBefore="end_op_marker" />

### Inputs and outputs

Each op has a set of inputs and outputs, which define the data it consumes and produces. Inputs and outputs are used to define dependencies between ops and to pass data between ops.

Both definitions have a few important properties:

- They are named.
- They are optionally typed. These types are validated at runtime.
- (Advanced) They can be linked to an <PyObject section="io-managers" module="dagster" object="IOManager"/>, which defines how the output or input is stored and loaded. See the [IO manager concept page](/guides/build/io-managers/) for more info.

#### Inputs

Inputs are passed as arguments to an op's `compute_fn`. The value of an input can be passed from the output of another op, or [stubbed (hardcoded) using config](/guides/build/jobs/unconnected-inputs#loading-a-built-in-dagster-type-from-config).

The most common way to define inputs is just to add arguments to the decorated function:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_input_op_marker" endBefore="end_input_op_marker" />

An op only starts to execute once all of its inputs have been resolved. Inputs can be resolved in two ways:

- The upstream output that the input depends on has been successfully emitted and stored.
- The input was stubbed through config.

You can use a [Dagster Type](/api/python-api/types) to provide a function that validates an op's input every time the op runs. In this case, you use a dictionary of <PyObject section="ops" module="dagster" object="In" pluralize /> corresponding to the decorated function arguments.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_typed_input_op_marker" endBefore="end_typed_input_op_marker" />

#### Outputs

Outputs are yielded from an op's `compute_fn`. By default, all ops have a single output called "result".

When you have one output, you can return the output value directly.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_output_op_marker" endBefore="end_output_op_marker" />

To define multiple outputs, or to use a different output name than "result", you can provide a dictionary of <PyObject section="ops" module="dagster"  object="Out" pluralize /> to the <PyObject section="ops" module="dagster" object="op" object="op" decorator /> decorator.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_multi_output_op_marker" endBefore="end_multi_output_op_marker" />

Return type annotations can be used directly on ops. For a single output, the return annotation will be used directly for type checking.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_return_annotation" endBefore="end_return_annotation" />

If there are multiple outputs, a tuple annotation can be specified. Each inner type of the tuple annotation should correspond to an output in the op.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_tuple_return" endBefore="end_tuple_return" />

Outputs are expected to follow the order they are specified in the op's `out` dictionary. In the above example, the `int` output corresponds to `int_output`, and the `str` output corresponds to `str_output`.

Note that if you would like to specify a single tuple output and still utilize type annotations, this can be done by providing either a single <PyObject section="ops" module="dagster"  object="Out" /> to the op, or none.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_single_output_tuple" endBefore="end_single_output_tuple" />

Like inputs, outputs can also have [Dagster Types](/api/python-api/types).

While many use cases can be served using built-in python annotations, <PyObject section="ops" module="dagster" object="Output"/> and <PyObject section="dynamic" module="dagster" object="DynamicOutput"/> objects unlock additional functionality. Check out the docs on [Op Outputs](/guides/build/ops/op-events#output-objects) to learn more.

### Op configuration

Ops in Dagster can specify a config schema which makes them configurable and parameterizable at execution time. The configuration system is explained in detail in the [Config schema documentation](/guides/operate/configuration/run-configuration).

Op functions can specify an annotated `config` parameter for the op's configuration. The config class, which subclasses <PyObject section="config" module="dagster" object="Config"/> (which wraps [`pydantic.BaseModel`](https://docs.pydantic.dev/usage/models/#basic-model-usage)) specifies the configuration schema for the op. Op configuration can be used to specify op behavior at runtime, making ops more flexible and reusable.

For example, we can define an op where the API endpoint it queries is defined through its configuration:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_configured_op_marker" endBefore="end_configured_op_marker" />

### Op context

When writing an op, users can optionally provide a first parameter, `context`. When this parameter is supplied, Dagster will supply a context object to the body of the op. The context provides access to system information like loggers and the current run id. See <PyObject section="execution" module="dagster" object="OpExecutionContext"/> for the full list of properties accessible from the op context.

For example, to access the logger and log a info message:

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_op_context_marker" endBefore="end_op_context_marker" />

## Using an op

Ops are used within a [job](/guides/build/jobs/op-jobs) or [graph](/guides/build/ops/graphs). You can also execute a single op, usually within a test context, by directly invoking it. More information can be found at [Testing ops](/guides/test/unit-testing-assets-and-ops).

## Patterns

### Op factory

You may find the need to create utilities that help generate ops. In most cases, you should parameterize op behavior by adding op configuration. You should reach for this pattern if you find yourself needing to vary the arguments to the <PyObject section="ops" module="dagster" object="op" object="op" decorator /> decorator or <PyObject section="ops" module="dagster" object="OpDefinition"/> themselves, since they cannot be modified based on op configuration.

To create an op factory, you define a function that returns an <PyObject section="ops" module="dagster" object="OpDefinition"/>, either directly or by decorating a function with the op decorator.

<CodeExample path="docs_snippets/docs_snippets/concepts/ops_jobs_graphs/ops.py" startAfter="start_op_factory_pattern_marker" endBefore="end_op_factory_pattern_marker" />
