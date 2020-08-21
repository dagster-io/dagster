import datetime

import pandas as pd
from dagster_pandas import DataFrame

from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    check,
    execute_pipeline,
    execute_solid,
    lambda_solid,
)
from dagster.core.test_utils import single_output_solid


def _dataframe_solid(name, input_defs, compute_fn):
    return single_output_solid(
        name=name,
        input_defs=input_defs,
        compute_fn=compute_fn,
        output_def=OutputDefinition(DataFrame),
    )


def get_solid_result_value(solid_inst):
    pipe = PipelineDefinition(
        solid_defs=[load_num_csv_solid("load_csv"), solid_inst],
        dependencies={
            solid_inst.name: {
                list(solid_inst.input_dict.values())[0].name: DependencyDefinition("load_csv")
            }
        },
    )

    pipeline_result = execute_pipeline(pipe)

    execution_result = pipeline_result.result_for_solid(solid_inst.name)

    return execution_result.output_value()


def get_num_csv_environment(solids_config):
    return {"solids": solids_config}


def create_sum_table():
    def compute(_context, inputs):
        num_csv = inputs["num_csv"]
        check.inst_param(num_csv, "num_csv", pd.DataFrame)
        num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
        return num_csv

    return _dataframe_solid(
        name="sum_table", input_defs=[InputDefinition("num_csv", DataFrame)], compute_fn=compute
    )


@lambda_solid(
    input_defs=[InputDefinition("num_csv", DataFrame)], output_def=OutputDefinition(DataFrame)
)
def sum_table(num_csv):
    check.inst_param(num_csv, "num_csv", pd.DataFrame)
    num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
    return num_csv


@lambda_solid(
    input_defs=[InputDefinition("sum_df", DataFrame)], output_def=OutputDefinition(DataFrame)
)
def sum_sq_table(sum_df):
    sum_df["sum_squared"] = sum_df["sum"] * sum_df["sum"]
    return sum_df


@lambda_solid(
    input_defs=[InputDefinition("sum_table_renamed", DataFrame)],
    output_def=OutputDefinition(DataFrame),
)
def sum_sq_table_renamed_input(sum_table_renamed):
    sum_table_renamed["sum_squared"] = sum_table_renamed["sum"] * sum_table_renamed["sum"]
    return sum_table_renamed


def test_pandas_csv_in_memory():
    df = get_solid_result_value(create_sum_table())
    assert isinstance(df, pd.DataFrame)
    assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7]}


def _sum_only_pipeline():
    return PipelineDefinition(solid_defs=[sum_table, sum_sq_table], dependencies={})


def test_two_input_solid():
    def compute(_context, inputs):
        num_csv1 = inputs["num_csv1"]
        num_csv2 = inputs["num_csv2"]
        check.inst_param(num_csv1, "num_csv1", pd.DataFrame)
        check.inst_param(num_csv2, "num_csv2", pd.DataFrame)
        num_csv1["sum"] = num_csv1["num1"] + num_csv2["num2"]
        return num_csv1

    two_input_solid = _dataframe_solid(
        name="two_input_solid",
        input_defs=[InputDefinition("num_csv1", DataFrame), InputDefinition("num_csv2", DataFrame)],
        compute_fn=compute,
    )

    pipe = PipelineDefinition(
        solid_defs=[
            load_num_csv_solid("load_csv1"),
            load_num_csv_solid("load_csv2"),
            two_input_solid,
        ],
        dependencies={
            "two_input_solid": {
                "num_csv1": DependencyDefinition("load_csv1"),
                "num_csv2": DependencyDefinition("load_csv2"),
            }
        },
    )

    pipeline_result = execute_pipeline(pipe)
    assert pipeline_result.success

    df = pipeline_result.result_for_solid("two_input_solid").output_value()

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict("list") == {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7]}


def test_no_compute_solid():
    num_table = _dataframe_solid(
        name="num_table",
        input_defs=[InputDefinition("num_csv", DataFrame)],
        compute_fn=lambda _context, inputs: inputs["num_csv"],
    )
    df = get_solid_result_value(num_table)
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


def _result_for_solid(results, name):
    for result in results:
        if result.name == name:
            return result

    check.failed("could not find name")


def load_num_csv_solid(name):
    @lambda_solid(name=name)
    def _return_num_csv():
        return pd.DataFrame({"num1": [1, 3], "num2": [2, 4]})

    return _return_num_csv


def test_pandas_multiple_inputs():
    def compute_fn(_context, inputs):
        return inputs["num_csv1"] + inputs["num_csv2"]

    double_sum = _dataframe_solid(
        name="double_sum",
        input_defs=[InputDefinition("num_csv1", DataFrame), InputDefinition("num_csv2", DataFrame)],
        compute_fn=compute_fn,
    )

    pipe = PipelineDefinition(
        solid_defs=[load_num_csv_solid("load_one"), load_num_csv_solid("load_two"), double_sum],
        dependencies={
            "double_sum": {
                "num_csv1": DependencyDefinition("load_one"),
                "num_csv2": DependencyDefinition("load_two"),
            }
        },
    )

    output_df = execute_pipeline(pipe).result_for_solid("double_sum").output_value()

    assert not output_df.empty

    assert output_df.to_dict("list") == {"num1": [2, 6], "num2": [4, 8]}


def test_rename_input():
    result = execute_pipeline(
        PipelineDefinition(
            solid_defs=[load_num_csv_solid("load_csv"), sum_table, sum_sq_table_renamed_input],
            dependencies={
                "sum_table": {"num_csv": DependencyDefinition("load_csv")},
                sum_sq_table_renamed_input.name: {
                    "sum_table_renamed": DependencyDefinition(sum_table.name)
                },
            },
        )
    )

    assert result.success

    expected = {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7], "sum_squared": [9, 49]}
    solid_result = result.result_for_solid("sum_sq_table_renamed_input")
    assert solid_result.output_value().to_dict("list") == expected


def test_date_column():
    @lambda_solid(output_def=OutputDefinition(DataFrame))
    def dataframe_constant():
        return pd.DataFrame([{datetime.date(2019, 1, 1): 0}])

    assert execute_solid(dataframe_constant).success
