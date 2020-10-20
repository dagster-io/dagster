import re
import shutil

import dask.dataframe as dd
import pytest
from dagster import InputDefinition, OutputDefinition, execute_solid, file_relative_path, solid
from dagster.utils.test import get_temp_dir
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

    # https://github.com/dagster-io/dagster/issues/2872
    with pytest.warns(
        UserWarning,
        match=re.escape(
            "Specifying {key}: is deprecated. Use read:{key}: instead.".format(key=file_type)
        ),
    ):
        file_name = file_relative_path(__file__, f"num.{file_type}")
        result = execute_solid(
            return_df,
            run_config={
                "solids": {"return_df": {"inputs": {"input_df": {file_type: {"path": file_name}}}}}
            },
        )
        assert result.success
        assert assert_eq(result.output_value(), create_dask_df())

    read_result = execute_solid(
        return_df,
        run_config={
            "solids": {
                "return_df": {"inputs": {"input_df": {"read": {file_type: {"path": file_name}}}}}
            }
        },
    )
    assert read_result.success
    assert assert_eq(result.output_value(), read_result.output_value())


@pytest.mark.parametrize(
    "file_type,read,kwargs",
    [
        pytest.param("csv", dd.read_csv, {"index": False}, id="csv"),
        pytest.param("parquet", dd.read_parquet, {"write_index": False}, id="parquet"),
        pytest.param("json", dd.read_json, {}, id="json"),
    ],
)
def test_dataframe_outputs(file_type, read, kwargs):
    df = create_dask_df()

    @solid(output_defs=[OutputDefinition(dagster_type=DataFrame, name="output_df")])
    def return_df(_):
        return df

    # https://github.com/dagster-io/dagster/issues/2872
    with pytest.warns(
        UserWarning,
        match=re.escape(
            "Specifying {key}: is deprecated. Use to:{key}: instead.".format(key=file_type)
        ),
    ):
        with get_temp_dir() as temp_path:
            shutil.rmtree(temp_path)
            result = execute_solid(
                return_df,
                run_config={
                    "solids": {
                        "return_df": {
                            "outputs": [{"output_df": {file_type: {"path": temp_path, **kwargs}}}]
                        }
                    }
                },
            )
            assert result.success
            actual = read(f"{temp_path}/*")
            assert assert_eq(actual, df)


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
