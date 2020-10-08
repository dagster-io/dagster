from dagster_pandas import DataFrame

from dagster import InputDefinition, OutputDefinition, execute_solid, lambda_solid
from dagster.core.test_utils import single_output_solid
from dagster.utils import file_relative_path


def create_num_csv_environment():
    return {
        "solids": {
            "hello_world": {
                "inputs": {"num_csv": {"csv": {"path": file_relative_path(__file__, "num.csv")}}}
            }
        }
    }


def test_hello_world_with_dataframe_fns():
    hello_world = create_definition_based_solid()
    run_hello_world(hello_world)


def run_hello_world(hello_world):
    assert len(hello_world.input_dict) == 1

    result = execute_solid(hello_world, run_config=create_num_csv_environment())

    assert result.success

    assert result.output_value().to_dict("list") == {"num1": [1, 3], "num2": [2, 4], "sum": [3, 7]}


def create_definition_based_solid():
    table_input = InputDefinition("num_csv", DataFrame)

    def compute_fn(_context, inputs):
        num_csv = inputs["num_csv"]
        num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
        return num_csv

    # supports CSV and PARQUET by default
    hello_world = single_output_solid(
        name="hello_world",
        input_defs=[table_input],
        compute_fn=compute_fn,
        output_def=OutputDefinition(DataFrame),
    )

    return hello_world


def create_decorator_based_solid():
    @lambda_solid(
        input_defs=[InputDefinition("num_csv", DataFrame)], output_def=OutputDefinition(DataFrame)
    )
    def hello_world(num_csv):
        num_csv["sum"] = num_csv["num1"] + num_csv["num2"]
        return num_csv

    return hello_world


def test_hello_world_decorator_style():
    hello_world = create_decorator_based_solid()
    run_hello_world(hello_world)
