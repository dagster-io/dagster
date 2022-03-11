import os

import pandas as pd
import pytest
from dagster_pandas import DataFrame

from dagster import DagsterInvalidConfigError, In, Out, graph, op
from dagster._utils import file_relative_path
from dagster._utils.test import get_temp_file_name


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

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @graph
    def test_graph():
        return df_as_config()

    result = test_graph.execute_in_process(
        run_config={
            "ops": {
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

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        # this is the pandas behavior
        assert df.to_dict("list") == {"num1,num2": ["1,2", "3,4"]}
        called["yup"] = True

    @graph
    def test_graph():
        return df_as_config()

    result = test_graph.execute_in_process(
        run_config={
            "ops": {
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

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @graph
    def test_graph():
        return df_as_config()

    result = test_graph.execute_in_process(
        run_config={
            "ops": {
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

    @op(ins={"df": In(DataFrame)})
    def df_as_input(_context, df):  # pylint: disable=W0613
        called["yup"] = True

    @graph
    def missing_inputs():
        return df_as_input()

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        missing_inputs.execute_in_process()

    assert len(exc_info.value.errors) == 1

    expected_suggested_config = {"df_as_input": {"inputs": {"df": "<selector>"}}}
    assert exc_info.value.errors[0].message.startswith(
        'Missing required config entry "ops" at the root.'
    )
    assert str(expected_suggested_config) in exc_info.value.errors[0].message

    assert "yup" not in called


def test_dataframe_csv_missing_input_collision():
    called = {}

    @op(out=Out(DataFrame))
    def df_as_output(_context):
        return pd.DataFrame()

    @op(ins={"df": In(DataFrame)})
    def df_as_input(_context, df):  # pylint: disable=W0613
        called["yup"] = True

    @graph
    def overlapping():
        return df_as_input(df_as_output())

    with pytest.raises(DagsterInvalidConfigError) as exc_info:
        overlapping.execute_in_process(
            run_config={
                "ops": {
                    "df_as_input": {
                        "inputs": {"df": {"csv": {"path": file_relative_path(__file__, "num.csv")}}}
                    }
                }
            },
        )

    assert (
        'Error 1: Received unexpected config entry "inputs" at path root:ops:df_as_input.'
        in str(exc_info.value)
    )

    assert "yup" not in called


def test_dataframe_parquet_from_inputs():
    check_parquet_support()

    called = {}

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @graph
    def test_graph():
        df_as_config()

    result = test_graph.execute_in_process(
        run_config={
            "ops": {
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

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @graph
    def test_graph():
        df_as_config()

    result = test_graph.execute_in_process(
        run_config={
            "ops": {
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


def test_dataframe_pickle_from_inputs():
    # python2.7 doesn't like DataFrame pickles created from python3.x and vice versa. So we create them on-the-go
    pickle_path = file_relative_path(__file__, "num.pickle")
    df = pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})
    df.to_pickle(pickle_path)

    called = {}

    @op(ins={"df": In(DataFrame)})
    def df_as_config(_context, df):
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
        called["yup"] = True

    @graph
    def test_graph():
        df_as_config()

    result = test_graph.execute_in_process(
        run_config={"ops": {"df_as_config": {"inputs": {"df": {"pickle": {"path": pickle_path}}}}}}
    )

    assert result.success
    assert called["yup"]

    os.remove(pickle_path)


def test_dataframe_csv_materialization():
    @op(out=Out(DataFrame))
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @graph
    def return_df_graph():
        return_df()

    with get_temp_file_name() as filename:
        result = return_df_graph.execute_in_process(
            run_config={
                "ops": {"return_df": {"outputs": [{"result": {"csv": {"path": filename}}}]}}
            },
        )

        assert result.success

        df = pd.read_csv(filename)
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def test_dataframe_parquet_materialization():
    check_parquet_support()

    @op(out=Out(DataFrame))
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @graph
    def return_df_graph():
        return_df()

    with get_temp_file_name() as filename:
        result = return_df_graph.execute_in_process(
            run_config={
                "ops": {"return_df": {"outputs": [{"result": {"parquet": {"path": filename}}}]}}
            },
        )

        assert result.success

        df = pd.read_parquet(filename)
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def test_dataframe_table_materialization():
    @op(out=Out(DataFrame))
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @graph
    def return_df_graph():
        return_df()

    with get_temp_file_name() as filename:
        filename = "/tmp/table_test.txt"
        result = return_df_graph.execute_in_process(
            run_config={
                "ops": {"return_df": {"outputs": [{"result": {"table": {"path": filename}}}]}}
            },
        )

        assert result.success

        df = pd.read_csv(filename, sep="\t")
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def test_dataframe_pickle_materialization():
    @op(out=Out(DataFrame))
    def return_df(_context):
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    @graph
    def return_df_graph():
        return_df()

    with get_temp_file_name() as filename:
        filename = "/tmp/num.pickle"
        result = return_df_graph.execute_in_process(
            run_config={
                "ops": {"return_df": {"outputs": [{"result": {"pickle": {"path": filename}}}]}}
            },
        )

        assert result.success

        df = pd.read_pickle(filename)
        assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}
