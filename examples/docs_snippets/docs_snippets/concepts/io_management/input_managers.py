import os
from typing import Any

import numpy as np
import pandas as pd

from dagster import (
    ConfigurableIOManager,
    In,
    InputContext,
    InputManager,
    OutputContext,
    input_manager,
    job,
    op,
)


class PandasIOManager(ConfigurableIOManager):
    def handle_output(self, context: OutputContext, obj):
        pass

    def load_input(self, context: InputContext):
        pass


class TableIOManager(ConfigurableIOManager):
    def handle_output(self, context: OutputContext, obj):
        pass

    def load_input(self, context: InputContext):
        pass


@op
def produce_pandas_output():
    return 1


def read_dataframe_from_table(*_args, **_kwargs):
    pass


def write_dataframe_to_table(*_args, **_kwargs):
    pass


pd_series_io_manager: Any = None

# start_different_input_managers


@op
def op_1():
    return [1, 2, 3]


@op(ins={"a": In(input_manager_key="pandas_series")})
def op_2(a):
    return pd.concat([a, pd.Series([4, 5, 6])])


@job(resource_defs={"pandas_series": pd_series_io_manager})
def a_job():
    op_2(op_1())


# end_different_input_managers

# start_plain_input_manager


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


# end_plain_input_manager


# start_better_input_manager


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


# end_better_input_manager

# start_load_unconnected_via_fn


@input_manager
def simple_table_1_manager():
    return read_dataframe_from_table(name="table_1")


@op(ins={"dataframe": In(input_manager_key="simple_load_input_manager")})
def my_op(dataframe):
    """Do some stuff."""
    dataframe.head()


@job(resource_defs={"simple_load_input_manager": simple_table_1_manager})
def simple_load_table_job():
    my_op()


# end_load_unconnected_via_fn

# start_load_unconnected_input


class Table1InputManager(InputManager):
    def load_input(self, context: InputContext):
        return read_dataframe_from_table(name="table_1")


@input_manager
def table_1_manager():
    return Table1InputManager()


@job(resource_defs={"load_input_manager": table_1_manager})
def load_table_job():
    my_op()


# end_load_unconnected_input


# start_load_unconnected_io
# in this example, TableIOManager is defined elsewhere and we just want to override load_input
class Table1IOManager(TableIOManager):
    def load_input(self, context: InputContext):
        return read_dataframe_from_table(name="table_1")


@job(resource_defs={"load_input_manager": Table1IOManager()})
def io_load_table_job():
    my_op()


# end_load_unconnected_io

# start_load_input_subset


class MyIOManager(ConfigurableIOManager):
    def handle_output(self, context: OutputContext, obj):
        table_name = context.name
        write_dataframe_to_table(name=table_name, dataframe=obj)

    def load_input(self, context: InputContext):
        if context.upstream_output:
            return read_dataframe_from_table(name=context.upstream_output.name)


@input_manager
def my_subselection_input_manager():
    return read_dataframe_from_table(name="table_1")


@op
def op1():
    """Do stuff."""


@op(ins={"dataframe": In(input_manager_key="my_input_manager")})
def op2(dataframe):
    """Do stuff."""
    dataframe.head()


@job(
    resource_defs={
        "io_manager": MyIOManager(),
        "my_input_manager": my_subselection_input_manager,
    }
)
def my_subselection_job():
    op2(op1())


# end_load_input_subset

# start_better_load_input_subset


class MyNewInputLoader(MyIOManager):
    def load_input(self, context: InputContext):
        if context.upstream_output is None:
            # load input from table since there is no upstream output
            return read_dataframe_from_table(name="table_1")
        else:
            return super().load_input(context)


# end_better_load_input_subset

# start_execute_subselection
my_subselection_job.execute_in_process(
    op_selection=["op2"],
)

# end_execute_subselection


# start_per_input_config


class MyConfigurableInputLoader(InputManager):
    def load_input(self, context: InputContext):
        return read_dataframe_from_table(name=context.config["table"])


@input_manager(input_config_schema={"table": str})
def my_configurable_input_loader():
    return MyConfigurableInputLoader()


# or


@input_manager(input_config_schema={"table": str})
def my_other_configurable_input_loader(context):
    return read_dataframe_from_table(name=context.config["table"])


# end_per_input_config

# start_per_input_config_exec

load_table_job.execute_in_process(
    run_config={"ops": {"my_op": {"inputs": {"dataframe": {"table": "table_1"}}}}},
)
# end_per_input_config_exec
