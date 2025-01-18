---
title: "Defining a custom I/O manager"
sidebar_position: 100
---

If you have specific requirements for where and how your outputs should be stored and retrieved, you can define a custom I/O manager. This boils down to implementing two functions: one that stores outputs and one that loads inputs.

To define an I/O manager, extend the <PyObject section="io-managers" module="dagster" object="IOManager" /> class. Often, you will want to extend the <PyObject section="io-managers" module="dagster" object="ConfigurableIOManager"/> class (which subclasses `IOManager`) to attach a config schema to your I/O manager.

Here, we define a simple I/O manager that reads and writes CSV values to the filesystem. It takes an optional prefix path through config.

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/custom_io_manager.py startafter=start_io_manager_marker endbefore=end_io_manager_marker
from dagster import ConfigurableIOManager, InputContext, OutputContext


class MyIOManager(ConfigurableIOManager):
    # specifies an optional string list input, via config system
    path_prefix: list[str] = []

    def _get_path(self, context) -> str:
        return "/".join(self.path_prefix + context.asset_key.path)

    def handle_output(self, context: OutputContext, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context: InputContext):
        return read_csv(self._get_path(context))
```

The provided `context` argument for `handle_output` is an <PyObject section="io-managers" module="dagster" object="OutputContext" />. The provided `context` argument for `load_input` is an <PyObject section="io-managers" module="dagster" object="InputContext" />. The linked API documentation lists all the fields that are available on these objects.

### Using an I/O manager factory

If your I/O manager is more complex, or needs to manage internal state, it may make sense to split out the I/O manager definition from its configuration. In this case, you can use <PyObject section="io-managers" module="dagster" object="ConfigurableIOManagerFactory"/>, which specifies config schema and implements a factory function that takes the config and returns an I/O manager.

In this case, we implement a stateful I/O manager which maintains a cache.

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/custom_io_manager.py startafter=start_io_manager_factory_marker endbefore=end_io_manager_factory_marker
from dagster import IOManager, ConfigurableIOManagerFactory, OutputContext, InputContext
import requests


class ExternalIOManager(IOManager):
    def __init__(self, api_token):
        self._api_token = api_token
        # setup stateful cache
        self._cache = {}

    def handle_output(self, context: OutputContext, obj): ...

    def load_input(self, context: InputContext):
        if context.asset_key in self._cache:
            return self._cache[context.asset_key]
        ...


class ConfigurableExternalIOManager(ConfigurableIOManagerFactory):
    api_token: str

    def create_io_manager(self, context) -> ExternalIOManager:
        return ExternalIOManager(self.api_token)
```

### Defining Pythonic I/O managers

Pythonic I/O managers are defined as subclasses of <PyObject section="io-managers" module="dagster" object="ConfigurableIOManager"/>, and similarly to [Pythonic resources](/todo) specify any configuration fields as attributes. Each subclass must implement a `handle_output` and `load_input` method, which are called by Dagster at runtime to handle the storing and loading of data.

{/* TODO convert to <CodeExample> */}
```python file=/concepts/resources/pythonic_resources.py startafter=start_new_io_manager endbefore=end_new_io_manager dedent=4
from dagster import (
    Definitions,
    AssetKey,
    OutputContext,
    InputContext,
    ConfigurableIOManager,
)

class MyIOManager(ConfigurableIOManager):
    root_path: str

    def _get_path(self, asset_key: AssetKey) -> str:
        return self.root_path + "/".join(asset_key.path)

    def handle_output(self, context: OutputContext, obj):
        write_csv(self._get_path(context.asset_key), obj)

    def load_input(self, context: InputContext):
        return read_csv(self._get_path(context.asset_key))

defs = Definitions(
    assets=...,
    resources={"io_manager": MyIOManager(root_path="/tmp/")},
)
```

### Handling partitioned assets

I/O managers can be written to handle [partitioned](/guides/build/partitions-and-backfills/partitioning-assets) assets. For a partitioned asset, each invocation of `handle_output` will (over)write a single partition, and each invocation of `load_input` will load one or more partitions. When the I/O manager is backed by a filesystem or object store, then each partition will typically correspond to a file or object. When it's backed by a database, then each partition will typically correspond to a range of rows in a table that fall within a particular window.

The default I/O manager has support for loading a partitioned upstream asset for a downstream asset with matching partitions out of the box (see the section below for loading multiple partitions). The <PyObject section="io-managers" module="dagster" object="UPathIOManager" /> can be used to handle partitions in custom filesystem-based I/O managers.

To handle partitions in an custom I/O manager, you'll need to determine which partition you're dealing with when you're storing an output or loading an input. For this, <PyObject section="io-managers" module="dagster" object="OutputContext" /> and <PyObject section="io-managers" module="dagster" object="InputContext" /> have a `asset_partition_key` property:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/custom_io_manager.py startafter=start_partitioned_marker endbefore=end_partitioned_marker
class MyPartitionedIOManager(IOManager):
    def _get_path(self, context) -> str:
        if context.has_partition_key:
            return "/".join(context.asset_key.path + [context.asset_partition_key])
        else:
            return "/".join(context.asset_key.path)

    def handle_output(self, context: OutputContext, obj):
        write_csv(self._get_path(context), obj)

    def load_input(self, context: InputContext):
        return read_csv(self._get_path(context))
```

If you're working with time window partitions, you can also use the `asset_partitions_time_window` property, which will return a <PyObject section="partitions" module="dagster" object="TimeWindow" /> object.

#### Handling partition mappings

A single partition of one asset might depend on a range of partitions of an upstream asset.

The default I/O manager has support for loading multiple upstream partitions. In this case, the downstream asset should use `Dict[str, ...]` (or leave it blank) type for the upstream `DagsterType`. Here is an example of loading multiple upstream partitions using the default partition mapping:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/loading_multiple_upstream_partitions.py
from datetime import datetime
from typing import Dict

import pandas as pd

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    HourlyPartitionsDefinition,
    asset,
    materialize,
)

start = datetime(2022, 1, 1)

hourly_partitions = HourlyPartitionsDefinition(start_date=f"{start:%Y-%m-%d-%H:%M}")
daily_partitions = DailyPartitionsDefinition(start_date=f"{start:%Y-%m-%d}")


@asset(partitions_def=hourly_partitions)
def upstream_asset(context: AssetExecutionContext) -> pd.DataFrame:
    return pd.DataFrame({"date": [context.partition_key]})


@asset(
    partitions_def=daily_partitions,
)
def downstream_asset(upstream_asset: dict[str, pd.DataFrame]) -> pd.DataFrame:
    return pd.concat(list(upstream_asset.values()))


result = materialize(
    [*upstream_asset.to_source_assets(), downstream_asset],
    partition_key=start.strftime(daily_partitions.fmt),
)
downstream_asset_data = result.output_for_node("downstream_asset", "result")
assert (
    len(downstream_asset_data) == 24
), "downstream day should map to upstream 24 hours"
```

The `upstream_asset` becomes a mapping from partition keys to partition values. This is a property of the default I/O manager or any I/O manager inheriting from the <PyObject section="io-managers" module="dagster" object="UPathIOManager" />.

A <PyObject section="partitions" module="dagster" object="PartitionMapping" /> can be provided to <PyObject section="assets" module="dagster" object="AssetIn" /> to configure the mapped upstream partitions.

When writing a custom I/O manager for loading multiple upstream partitions, the mapped keys can be accessed using <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partition_keys" />, <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partition_key_range" />, or <PyObject section="io-managers" module="dagster" object="InputContext" method="asset_partitions_time_window" />.

### Writing a per-input I/O manager

In some cases you may find that you need to load an input in a way other than the `load_input` function of the corresponding output's I/O manager. For example, let's say Team A has an op that returns an output as a Pandas DataFrame and specifies an I/O manager that knows how to store and load Pandas DataFrames. Your team is interested in using this output for a new op, but you are required to use PySpark to analyze the data. Unfortunately, you don't have permission to modify Team A's I/O manager to support this case. Instead, you can specify an input manager on your op that will override some of the behavior of Team A's I/O manager.

Since the method for loading an input is directly affected by the way the corresponding output was stored, we recommend defining your input managers as subclasses of existing I/O managers and just updating the `load_input` method. In this example, we load an input as a NumPy array rather than a Pandas DataFrame by writing the following:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/input_managers.py startafter=start_plain_input_manager endbefore=end_plain_input_manager
# in this case PandasIOManager is an existing IO Manager
class MyNumpyLoader(PandasIOManager):
    def load_input(self, context: InputContext) -> np.ndarray:
        file_path = "path/to/dataframe"
        array = np.genfromtxt(file_path, delimiter=",", dtype=None)
        return array


@op(ins={"np_array_input": In(input_manager_key="numpy_manager")})
def analyze_as_numpy(np_array_input: np.ndarray):
    assert isinstance(np_array_input, np.ndarray)


@job(resource_defs={"numpy_manager": MyNumpyLoader(), "io_manager": PandasIOManager()})
def my_job():
    df = produce_pandas_output()
    analyze_as_numpy(df)
```

This may quickly run into issues if the owner of `PandasIOManager` changes the path at which they store outputs. We recommend splitting out path defining logic (or other computations shared by `handle_output` and `load_input`) into new methods that are called when needed.

{/* TODO convert to <CodeExample> */}
```python file=/concepts/io_management/input_managers.py startafter=start_better_input_manager endbefore=end_better_input_manager
# this IO Manager is owned by a different team
class BetterPandasIOManager(ConfigurableIOManager):
    def _get_path(self, output_context):
        return os.path.join(
            self.base_dir,
            "storage",
            f"{output_context.step_key}_{output_context.name}.csv",
        )

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        file_path = self._get_path(context)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if obj is not None:
            obj.to_csv(file_path, index=False)

    def load_input(self, context: InputContext) -> pd.DataFrame:
        return pd.read_csv(self._get_path(context.upstream_output))


# write a subclass that uses _get_path for your custom loading logic
class MyBetterNumpyLoader(BetterPandasIOManager):
    def load_input(self, context: InputContext) -> np.ndarray:
        file_path = self._get_path(context.upstream_output)
        array = np.genfromtxt(file_path, delimiter=",", dtype=None)
        return array


@op(ins={"np_array_input": In(input_manager_key="better_numpy_manager")})
def better_analyze_as_numpy(np_array_input: np.ndarray):
    assert isinstance(np_array_input, np.ndarray)


@job(
    resource_defs={
        "numpy_manager": MyBetterNumpyLoader(),
        "io_manager": BetterPandasIOManager(),
    }
)
def my_better_job():
    df = produce_pandas_output()
    better_analyze_as_numpy(df)
```
