---
title: "Defining a custom I/O manager"
sidebar_position: 100
---

If you have specific requirements for where and how your outputs should be stored and retrieved, you can define a custom I/O manager. This boils down to implementing two functions: one that stores outputs and one that loads inputs.

To define an I/O manager, extend the <PyObject section="io-managers" module="dagster" object="IOManager" /> class. Often, you will want to extend the <PyObject section="io-managers" module="dagster" object="ConfigurableIOManager"/> class (which subclasses `IOManager`) to attach a config schema to your I/O manager.

Here, we define a simple I/O manager that reads and writes CSV values to the filesystem. It takes an optional prefix path through config.

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/custom_io_manager.py" startAfter="start_io_manager_marker" endBefore="end_io_manager_marker" />

The provided `context` argument for `handle_output` is an <PyObject section="io-managers" module="dagster" object="OutputContext" />. The provided `context` argument for `load_input` is an <PyObject section="io-managers" module="dagster" object="InputContext" />. The linked API documentation lists all the fields that are available on these objects.

### Using an I/O manager factory

If your I/O manager is more complex, or needs to manage internal state, it may make sense to split out the I/O manager definition from its configuration. In this case, you can use <PyObject section="io-managers" module="dagster" object="ConfigurableIOManagerFactory"/>, which specifies config schema and implements a factory function that takes the config and returns an I/O manager.

In this case, we implement a stateful I/O manager which maintains a cache:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/custom_io_manager.py" startAfter="start_io_manager_factory_marker" endBefore="end_io_manager_factory_marker" />

### Defining Pythonic I/O managers

Pythonic I/O managers are defined as subclasses of <PyObject section="io-managers" module="dagster" object="ConfigurableIOManager"/>, and similarly to [Pythonic resources](/guides/build/external-resources/) specify any configuration fields as attributes. Each subclass must implement a `handle_output` and `load_input` method, which are called by Dagster at runtime to handle the storing and loading of data.

{/* TODO add dedent=4 prop to CodeExample below when implemented */}
<CodeExample path="docs_snippets/docs_snippets/concepts/resources/pythonic_resources.py" startAfter="start_new_io_manager" endBefore="end_new_io_manager" />

### Handling partitioned assets

I/O managers can be written to handle [partitioned](/guides/build/partitions-and-backfills/partitioning-assets) assets. For a partitioned asset, each invocation of `handle_output` will (over)write a single partition, and each invocation of `load_input` will load one or more partitions. When the I/O manager is backed by a filesystem or object store, then each partition will typically correspond to a file or object. When it's backed by a database, then each partition will typically correspond to a range of rows in a table that fall within a particular window.

The default I/O manager has support for loading a partitioned upstream asset for a downstream asset with matching partitions out of the box (see the section below for loading multiple partitions). The <PyObject section="io-managers" module="dagster" object="UPathIOManager" /> can be used to handle partitions in custom filesystem-based I/O managers.

To handle partitions in an custom I/O manager, you'll need to determine which partition you're dealing with when you're storing an output or loading an input. For this, <PyObject section="io-managers" module="dagster" object="OutputContext" /> and <PyObject section="io-managers" module="dagster" object="InputContext" /> have a `asset_partition_key` property:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/custom_io_manager.py" startAfter="start_partitioned_marker" endBefore="end_partitioned_marker" />

If you're working with time window partitions, you can also use the `asset_partitions_time_window` property, which will return a <PyObject section="partitions" module="dagster" object="TimeWindow" /> object.

#### Handling partition mappings

A single partition of one asset might depend on a range of partitions of an upstream asset.

The default I/O manager has support for loading multiple upstream partitions. In this case, the downstream asset should use `Dict[str, ...]` (or leave it blank) type for the upstream `DagsterType`. Here is an example of loading multiple upstream partitions using the default partition mapping:


<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/loading_multiple_upstream_partitions.py" />

The `upstream_asset` becomes a mapping from partition keys to partition values. This is a property of the default I/O manager or any I/O manager inheriting from the <PyObject section="io-managers" module="dagster" object="UPathIOManager" />.

A <PyObject section="partitions" module="dagster" object="PartitionMapping" /> can be provided to <PyObject section="assets" module="dagster" object="AssetIn" /> to configure the mapped upstream partitions.

When writing a custom I/O manager for loading multiple upstream partitions, the mapped keys can be accessed using <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partition_keys" />, <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partition_key_range" />, or <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partitions_time_window" />.

### Writing a per-input I/O manager

In some cases you may find that you need to load an input in a way other than the `load_input` function of the corresponding output's I/O manager. For example, let's say Team A has an op that returns an output as a Pandas DataFrame and specifies an I/O manager that knows how to store and load Pandas DataFrames. Your team is interested in using this output for a new op, but you are required to use PySpark to analyze the data. Unfortunately, you don't have permission to modify Team A's I/O manager to support this case. Instead, you can specify an input manager on your op that will override some of the behavior of Team A's I/O manager.

Since the method for loading an input is directly affected by the way the corresponding output was stored, we recommend defining your input managers as subclasses of existing I/O managers and just updating the `load_input` method. In this example, we load an input as a NumPy array rather than a Pandas DataFrame by writing the following:

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_plain_input_manager" endBefore="end_plain_input_manager" />

This may quickly run into issues if the owner of `PandasIOManager` changes the path at which they store outputs. We recommend splitting out path defining logic (or other computations shared by `handle_output` and `load_input`) into new methods that are called when needed.

<CodeExample path="docs_snippets/docs_snippets/concepts/io_management/input_managers.py" startAfter="start_better_input_manager" endBefore="end_better_input_manager" />
