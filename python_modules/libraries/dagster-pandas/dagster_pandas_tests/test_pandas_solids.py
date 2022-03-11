import datetime

import pandas as pd
from dagster_pandas import DataFrame

from dagster import DependencyDefinition, GraphDefinition, In, Out, _check as check, graph, op


def get_op_result_value(op_inst):
    single_op_graph = GraphDefinition(
        name="test",
        description=None,
        node_defs=[load_num_csv_op("load_csv"), op_inst],
        dependencies={
            op_inst.name: {
                list(op_inst.input_dict.values())[0].name: DependencyDefinition("load_csv")
            }
        },
        input_mappings=None,
        output_mappings=None,
        config=None,
    )

    result = single_op_graph.execute_in_process()

    return result.output_for_node(op_inst.name)


def get_num_csv_environment(ops_config):
    return {"ops": ops_config}


@op(ins={"num_csv": In(DataFrame)}, out=Out(DataFrame))
def sum_table(_, num_csv):
    check.inst_param(num_csv, "num_csv", pd.DataFrame)
    num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
    return num_csv


@op(ins={"sum_df": In(DataFrame)}, out=Out(DataFrame))
def sum_sq_table(sum_df):
    sum_df["sum_squared"] = sum_df["sum"] * sum_df["sum"]
    return sum_df


@op(
    ins={"sum_table_renamed": In(DataFrame)},
    out=Out(DataFrame),
)
def sum_sq_table_renamed_input(sum_table_renamed):
    sum_table_renamed["sum_squared"] = sum_table_renamed["sum"] * sum_table_renamed["sum"]
    return sum_table_renamed


def test_pandas_csv_in_memory():
    df = get_op_result_value(sum_table)
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7]}


def test_two_input_op():
    @op(ins={"num_csv1": In(DataFrame), "num_csv2": In(DataFrame)})
    def two_input_op(_, num_csv1, num_csv2):
        check.inst_param(num_csv1, "num_csv1", pd.DataFrame)
        check.inst_param(num_csv2, "num_csv2", pd.DataFrame)
        num_csv1["sum"] = num_csv1["num1"] + num_csv2["num2"]
        return num_csv1

    load_csv1 = load_num_csv_op("load_csv1")
    load_csv2 = load_num_csv_op("load_csv2")

    @graph
    def two_input():
        two_input_op(load_csv1(), load_csv2())

    result = two_input.execute_in_process()
    assert result.success

    df = result.output_for_node("two_input_op")

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7]}


def test_no_compute_op():
    @op(ins={"num_csv": In(DataFrame)})
    def num_table(_, num_csv):
        return num_csv

    df = get_op_result_value(num_table)
    assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4]}


def create_diamond_deps():
    return {
        "num_table": {"num_csv": DependencyDefinition("load_csv")},
        "sum_table": {"num_table": DependencyDefinition("num_table")},
        "mult_table": {"num_table": DependencyDefinition("num_table")},
        "sum_mult_table": {
            "sum_table": DependencyDefinition("sum_table"),
            "mult_table": DependencyDefinition("mult_table"),
        },
    }


def load_num_csv_op(name):
    @op(name=name)
    def _return_num_csv():
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    return _return_num_csv


def test_pandas_multiple_inputs():
    @op(ins={"num_csv1": In(DataFrame), "num_csv2": In(DataFrame)})
    def double_sum(_, num_csv1, num_csv2):
        return num_csv1 + num_csv2

    load_one = load_num_csv_op("load_one")
    load_two = load_num_csv_op("load_two")

    @graph
    def multiple_inputs():
        double_sum(load_one(), load_two())

    output_df = multiple_inputs.execute_in_process().output_for_node("double_sum")

    assert not output_df.empty

    assert output_df.to_dict("list") == {"num1": [2, 6], "num2": [4, 8]}


def test_rename_input():
    load_csv = load_num_csv_op("load_csv")

    @graph
    def rename_input():
        sum_sq_table_renamed_input(sum_table(load_csv()))

    result = rename_input.execute_in_process()

    assert result.success

    expected = {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7], "sum_squared": [9, 49]}
    op_output = result.output_for_node("sum_sq_table_renamed_input")
    assert op_output.to_dict("list") == expected


def test_date_column():
    @op(out=Out(DataFrame))
    def dataframe_constant():
        return pd.DataFrame([{datetime.date(2019, 1, 1): 0}])

    df = dataframe_constant()
    assert isinstance(df, pd.DataFrame)
