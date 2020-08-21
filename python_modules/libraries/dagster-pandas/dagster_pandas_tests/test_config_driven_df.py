from __future__ import unicode_literals

import pandas as pd
import pytest
from dagster_pandas import DataFrame

from dagster import (
    DagsterInvalidConfigError,
    InputDefinition,
    OutputDefinition,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.utils import file_relative_path
from dagster.utils.test import get_temp_file_name


def check_parquet_support():
    try:
        import pyarrow  # pylint: disable=unused-import

        return
    except ImportError:
        pass

    try:
        import fastparquet  # pylint: disable=unused-import

        return
    except ImportError:
        pytest.skip("Skipping parquet test as neither pyarrow nor fastparquet is present.")


def test_dataframe_csv_from_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @pipeline
    def test_pipeline():
        return df_as_config()

    result = execute_pipeline(
        test_pipeline,
        {
            "solids": {
                "df_as_config": {
                    "inputs": {"df": {"csv": {"path": file_relative_path(__file__, "num.csv")}}}
                }
            }
        },
    )

    assert result.success
    assert called["yup"]


def test_dataframe_wrong_sep_from_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_config(_context, df):
        # this is the pandas behavior
        assert df.to_dict("list") == {"num1,num2": ["1,2", "3,4"]}
        called["yup"] = True

    @pipeline
    def test_pipeline():
        return df_as_config()

    result = execute_pipeline(
        test_pipeline,
        {
            "solids": {
                "df_as_config": {
                    "inputs": {
                        "df": {"csv": {"path": file_relative_path(__file__, "num.csv"), "sep": "|"}}
                    }
                }
            }
        },
    )

    assert result.success
    assert called["yup"]


def test_dataframe_pipe_sep_csv_from_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @pipeline
    def test_pipeline():
        return df_as_config()

    result = execute_pipeline(
        test_pipeline,
        {
            "solids": {
                "df_as_config": {
                    "inputs": {
                        "df": {
                            "csv": {
                                "path": file_relative_path(__file__, "num_pipes.csv"),
                                "sep": "|",
                            }
                        }
                    }
                }
            }
        },
    )

    assert result.success
    assert called["yup"]


def test_dataframe_csv_missing_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_input(_context, df):  # pylint: disable=W0613
        called["yup"] = True

    @pipeline
    def missing_inputs():
        return df_as_input()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(missing_inputs)

    assert len(exc_info.value.errors) == 1

    assert exc_info.value.errors[0].message == (
        """Missing required field "solids" at the root. """
        """Available Fields: "['execution', 'intermediate_storage', 'loggers', """
        """'resources', 'solids', 'storage']"."""
    )

    assert "yup" not in called


def test_dataframe_csv_missing_input_collision():
    called = {}

    @solid(output_defs=[OutputDefinition(DataFrame)])
    def df_as_output(_context):
        return pd.DataFrame()

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_input(_context, df):  # pylint: disable=W0613
        called["yup"] = True

    @pipeline
    def overlapping():
        return df_as_input(df_as_output())

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        execute_pipeline(
            overlapping,
            {
                "solids": {
                    "df_as_input": {
                        "inputs": {"df": {"csv": {"path": file_relative_path(__file__, "num.csv")}}}
                    }
                }
            },
        )

    assert 'Error 1: Undefined field "inputs" at path root:solids:df_as_input.' in str(
        exc_info.value
    )

    assert "yup" not in called


def test_dataframe_parquet_from_inputs():
    check_parquet_support()

    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @pipeline
    def test_pipeline():
        df_as_config()

    result = execute_pipeline(
        test_pipeline,
        {
            "solids": {
                "df_as_config": {
                    "inputs": {
                        "df": {"parquet": {"path": file_relative_path(__file__, "num.parquet")}}
                    }
                }
            }
        },
    )

    assert result.success
    assert called["yup"]


def test_dataframe_table_from_inputs():
    called = {}

    @solid(input_defs=[InputDefinition("df", DataFrame)])
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @pipeline
    def test_pipeline():
        df_as_config()

    result = execute_pipeline(
        test_pipeline,
        {
            "solids": {
                "df_as_config": {
                    "inputs": {
                        "df": {"table": {"path": file_relative_path(__file__, "num_table.txt")}}
                    }
                }
            }
        },
    )

    assert result.success
    assert called["yup"]


def test_dataframe_csv_materialization():
    @solid(output_defs=[OutputDefinition(DataFrame)])
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @pipeline
    def return_df_pipeline():
        return_df()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            return_df_pipeline,
            {"solids": {"return_df": {"outputs": [{"result": {"csv": {"path": filename}}}]}}},
        )

        assert result.success

        df = pd.read_csv(filename)
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def test_dataframe_parquet_materialization():
    check_parquet_support()

    @solid(output_defs=[OutputDefinition(DataFrame)])
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @pipeline
    def return_df_pipeline():
        return_df()

    with get_temp_file_name() as filename:
        result = execute_pipeline(
            return_df_pipeline,
            {"solids": {"return_df": {"outputs": [{"result": {"parquet": {"path": filename}}}]}}},
        )

        assert result.success

        df = pd.read_parquet(filename)
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def test_dataframe_table_materialization():
    @solid(output_defs=[OutputDefinition(DataFrame)])
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @pipeline
    def return_df_pipeline():
        return_df()

    with get_temp_file_name() as filename:
        filename = "/tmp/table_test.txt"
        result = execute_pipeline(
            return_df_pipeline,
            {"solids": {"return_df": {"outputs": [{"result": {"table": {"path": filename}}}]}}},
        )

        assert result.success

        df = pd.read_csv(filename, sep="\t")
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
