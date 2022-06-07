import os

import numpy as np
import pandas as pd
import pyspark.sql as pyspark

from dagster import (
    Field,
    IOManager,
    In,
    InputContext,
    Noneable,
    Out,
    OutputContext,
    graph,
    io_manager,
    op,
)


class PandasCsvIOManager(IOManager):
    def __init__(self, base_dir=None):
        self.base_dir = os.getenv("DAGSTER_HOME") if base_dir is None else base_dir

    def _get_path(self, output_context: OutputContext):
        return os.path.join(
            self.base_dir, "storage", f"{output_context.step_key}_{output_context.name}.csv"
        )

    def handle_output(self, context: OutputContext, obj: pd.DataFrame):
        file_path = self._get_path(context)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if obj is not None:
            obj.to_csv(file_path, index=False)

    def load_input(self, context: InputContext) -> pd.DataFrame:
        return pd.read_csv(self._get_path(context.upstream_output))  # type: ignore


@io_manager(config_schema={"base_dir": Field(Noneable(str), default_value=None, is_required=False)})
def pandas_io_manager(init_context):
    return PandasCsvIOManager(base_dir=init_context.resource_config["base_dir"])


class PysparkCsvInputManager(PandasCsvIOManager):
    def load_input(self, context: InputContext) -> pyspark.DataFrame:
        file_path = self._get_path(context.upstream_output)
        spark = pyspark.SparkSession.builder.getOrCreate()
        df = spark.read.csv(file_path)
        return df


@io_manager(config_schema={"base_dir": Field(Noneable(str), default_value=None, is_required=False)})
def pyspark_input_manager(init_context):
    return PysparkCsvInputManager(base_dir=init_context.resource_config["base_dir"])


class NumpyCsvInputManager(PandasCsvIOManager):
    def load_input(self, context: InputContext) -> np.ndarray:
        file_path = self._get_path(context.upstream_output)
        df = np.genfromtxt(file_path, delimiter=",", dtype=None)
        return df


@io_manager(config_schema={"base_dir": Field(Noneable(str), default_value=None, is_required=False)})
def numpy_input_manager(init_context):
    return NumpyCsvInputManager(base_dir=init_context.resource_config["base_dir"])


@op(out=Out(io_manager_key="pandas_io_mgr"))
def make_a_df():
    df = pd.DataFrame(
        {
            "ints": [1, 2, 3, 4],
            "floats": [1.0, 2.0, 3.0, 4.0],
            "strings": ["one", "two", "three", "four"],
        }
    )
    return df


@op
def avg_ints(context, df):
    avg = df["ints"].mean().item()
    context.log.info(f"Dataframe with type {type(df)} has average of the ints is {avg}")
    # return avg


@op
def median_floats(context, df):
    med = df["floats"].median().item()
    context.log.info(f"Dataframe with type {type(df)} has median of the floats is {med}")
    # return med


@op(
    ins={"df": In(input_manager_key="numpy_csv_mgr")},
    # required_resource_keys={"numpy_csv_mgr"}
)
def count_rows(context, df: np.ndarray):
    num_rows = df.shape[0]
    context.log.info(f"Dataframe with type {type(df)} has {num_rows} rows")
    # return num_rows


@graph
def df_stats():
    df = make_a_df()
    avg_ints(df)
    median_floats(df)
    # should be loaded as pyspark
    count_rows(df)


df_stats_job = df_stats.to_job(
    name="df_stats_job",
    resource_defs={
        "io_manager": pandas_io_manager,
        "pandas_io_mgr": pandas_io_manager,
        "pyspark_csv_mgr": pyspark_input_manager,
        "numpy_csv_mgr": numpy_input_manager,
    },
)
