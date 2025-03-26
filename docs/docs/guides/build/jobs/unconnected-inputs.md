---
title: 'Unconnected inputs in op jobs'
description: "Learn to work with unconnected inputs in op jobs."
sidebar_position: 400
---

import OpsNote from '@site/docs/partials/\_OpsNote.md';

<OpsNote />

Ops in a job may have input definitions that don't correspond to the outputs of upstream ops.

Values for these inputs can be provided in a few ways. Dagster will check the following, in order, and use the first available:

- **Input manager** - If the input to a job comes from an external source, such as a table in a database, you may want to define a resource responsible for loading it. This makes it easy to swap out implementations in different jobs and mock it in tests.

  A special I/O manager, which can be referenced from <PyObject section="ops" module="dagster" object="In" pluralize />, can be used to load unconnected inputs. Refer to the [I/O manager documentation](/guides/build/io-managers) for more information about I/O managers.

- **Dagster Type loader** - A <PyObject section="types" module="dagster" object="DagsterTypeLoader" /> provides a way to specify how to load inputs that depends on a type. A <PyObject section="types" module="dagster" object="DagsterTypeLoader" /> can be placed on <PyObject section="types" module="dagster" object="DagsterType" />, which can be placed on <PyObject section="ops" module="dagster" object="In" />.

- **Default values** - <PyObject section="ops" module="dagster" object="In" /> accepts a `default_value` argument.

**Unsure if I/O managers are right for you?** Check out the [Before you begin](/guides/build/io-managers/#before-you-begin) section of the I/O manager documentation.

## Working with Dagster types

### Loading a built-in Dagster type from config

When you have an op at the beginning of a job that operates on a built-in Dagster type like `string` or `int`, you can provide a value for that input via run config.

Here's a basic job with an unconnected string input:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/load_from_config.py" startAfter="def_start_marker" endBefore="def_end_marker" />

### Loading a custom Dagster type from config

When you have an op at the beginning of your job that operates on a Dagster type that you've defined, you can write your own <PyObject section="types" module="dagster" object="DagsterTypeLoader" /> to define how to load that input via run config.

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/load_custom_type_from_config.py" startAfter="def_start_marker" endBefore="def_end_marker" />

With this, the input can be specified via config as below:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/load_custom_type_from_config.py" startAfter="execute_start_marker" endBefore="execute_end_marker" />

## Working with input managers

### Providing an input manager for unconnected inputs

When you have an op at the beginning of a job that operates on data from an external source, you might wish to separate that I/O from your op's business logic, in the same way you would with an I/O manager if the op were loading from an upstream output.

Use the following tabs to learn about how to achieve this in Dagster.

<Tabs>
<TabItem value="Option 1: Use the input_manager decorator">

In this example, we wrote a function to load the input and decorated it with <PyObject section="io-managers" module="dagster" object="input_manager" decorator/>:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_load_unconnected_via_fn" endBefore="end_load_unconnected_via_fn" />

</TabItem>
<TabItem value="Option 2: Use a class to implement the InputManager interface">

In this example, we defined a class that implements the <PyObject section="io-managers" module="dagster" object="InputManager" /> interface:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_load_unconnected_input" endBefore="end_load_unconnected_input" />

To use `Table1InputManager` to store outputs or override the `load_input` method of an I/O manager used elsewhere in the job, another option is to implement an instance of <PyObject section="io-managers" module="dagster" object="IOManager" />:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_load_unconnected_io" endBefore="end_load_unconnected_io" />

</TabItem>
</Tabs>

In any of the examples in Option 1 or Option 2, setting the `input_manager_key` on an `In` controls how that input is loaded.

### Providing per-input config to input managers

When launching a run, you might want to parameterize how particular inputs are loaded.

To accomplish this, you can define an `input_config_schema` on the I/O manager or input manager definition. The `load_input` function can access this config when storing or loading data, via the <PyObject section="io-managers" module="dagster" object="InputContext" />:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_per_input_config" endBefore="end_per_input_config" />

Then, when executing a job, you can pass in this per-input config:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_per_input_config_exec" endBefore="end_per_input_config_exec" />

### Using input managers with subselection

You might want to execute a subset of ops in your job and control how the inputs of those ops are loaded. Custom input managers also help in these situations, because the inputs at the beginning of the subset become unconnected inputs.

For example, you might have `op1` that normally produces a table that `op2` consumes. To debug `op2`, you might want to run it on a different table than the one normally produced by `op1`.

To accomplish this, you can set up the `input_manager_key` on `op2`'s `In` to point to an input manager with the desired loading behavior. As in the previous example, setting the `input_manager_key` on an `In` controls how that input is loaded and you can write custom loading logic.

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_load_input_subset" endBefore="end_load_input_subset" />

So far, this is set up so that `op2` always loads `table_1` even if you execute the full job. This would let you debug `op2`, but if you want to write this so that `op2` only loads `table_1` when no input is provided from an upstream op, you can rewrite the input manager as a subclass of the IO manager used for the rest of the job as follows:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_better_load_input_subset" endBefore="end_better_load_input_subset" />

Now, when running the full job, `op2`'s input will be loaded using the IO manager on the output of `op1`. When running the job subset, `op2`'s input has no upstream output, so `table_1` will be loaded.

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_execute_subselection" endBefore="end_execute_subselection" />

## Relevant APIs

| Name                                                                 | Description                                                                      |
| -------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| <PyObject section="types" module="dagster" object="dagster_type_loader" decorator /> | The decorator used to define a Dagster Type Loader.                              |
| <PyObject section="types" module="dagster" object="DagsterTypeLoader" />             | The base class used to specify how to load inputs that depends on the type.      |
| <PyObject section="types" module="dagster" object="DagsterTypeLoaderContext" />      | The context object provided to the function decorated by `@dagster_type_loader`. |
| <PyObject section="io-managers" module="dagster" object="input_manager" decorator />       | The decorator used to define an input manager.                                   |
| <PyObject section="io-managers" module="dagster" object="InputManager" />                  | The base class used to specify how to load inputs.                               |