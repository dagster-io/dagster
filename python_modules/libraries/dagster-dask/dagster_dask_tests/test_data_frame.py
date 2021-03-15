import dask.dataframe as dd
import pytest
from dagster import InputDefinition, execute_solid, file_relative_path, solid
from dagster_dask import DataFrame
from dagster_dask.data_frame import DataFrameReadTypes, DataFrameToTypes
from dagster_dask.utils import DataFrameUtilities
from dask.dataframe.utils import assert_eq


def create_dask_df():
    path = file_relative_path(__file__, "num.csv")
    return dd.read_csv(path)


@pytest.mark.parametrize(
    "file_type",
    [
        pytest.param("csv", id="csv"),
        pytest.param("parquet", id="parquet"),
        pytest.param("json", id="json"),
    ],
)
def test_dataframe_inputs(file_type):
    @solid(input_defs=[InputDefinition(dagster_type=DataFrame, name="input_df")])
    def return_df(_, input_df):
        return input_df

    file_name = file_relative_path(__file__, f"num.{file_type}")

    read_result = execute_solid(
        return_df,
        run_config={
            "solids": {
                "return_df": {"inputs": {"input_df": {"read": {file_type: {"path": file_name}}}}}
            }
        },
    )
    assert read_result.success
    assert assert_eq(read_result.output_value(), create_dask_df())


def test_dataframe_loader_config_keys_dont_overlap():
    """
    Test that the read_keys, which are deprecated, do not overlap with
    the normal loader config_keys.
    """
    config_keys = set(DataFrameUtilities.keys())
    config_keys.add("read")
    read_keys = set(DataFrameReadTypes.keys())

    assert len(config_keys.intersection(read_keys)) == 0


def test_dataframe_materializer_config_keys_dont_overlap():
    """
    Test that the to_keys, which are deprecated, do not overlap with
    the normal materializer config_keys.
    """
    config_keys = set(DataFrameUtilities.keys())
    config_keys.add("to")
    to_keys = set(DataFrameToTypes.keys())

    assert len(config_keys.intersection(to_keys)) == 0
