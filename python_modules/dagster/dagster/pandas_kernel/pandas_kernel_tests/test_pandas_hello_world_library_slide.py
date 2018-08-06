import pandas as pd

import dagster
from dagster import config
from dagster.core.execution import (execute_single_solid, output_single_solid)
from dagster.core.decorators import solid
from dagster.utils.test import (script_relative_path, get_temp_file_name)

import dagster.pandas_kernel as dagster_pd


def create_num_csv_environment():
    return config.Environment(
        sources={
            'hello_world': {
                'num_csv': config.Source('CSV', {'path': script_relative_path('num.csv')})
            }
        }
    )


def test_hello_world_with_dataframe_fns():
    hello_world = create_definition_based_solid()
    run_hello_world(hello_world)


def run_hello_world(hello_world):
    result = execute_single_solid(
        dagster.ExecutionContext(),
        hello_world,
        environment=create_num_csv_environment(),
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    with get_temp_file_name() as temp_file_name:
        output_result = output_single_solid(
            dagster.ExecutionContext(),
            hello_world,
            environment=create_num_csv_environment(),
            name='CSV',
            arg_dict={'path': temp_file_name},
        )

        assert output_result.success

        assert pd.read_csv(temp_file_name).to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }


def create_definition_based_solid():
    table_input = dagster.InputDefinition('num_csv', dagster_pd.DataFrame)

    def transform_fn(_context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    # supports CSV and PARQUET by default
    hello_world = dagster.SolidDefinition(
        name='hello_world',
        inputs=[table_input],
        transform_fn=transform_fn,
        output=dagster.OutputDefinition(dagster_pd.DataFrame)
    )
    return hello_world


def create_decorator_based_solid():
    @solid(
        inputs=[dagster.InputDefinition('num_csv', dagster_pd.DataFrame)],
        output=dagster.OutputDefinition(dagster_pd.DataFrame),
    )
    def hello_world(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    return hello_world


def test_hello_world_decorator_style():
    hello_world = create_decorator_based_solid()
    run_hello_world(hello_world)
    result = execute_single_solid(
        dagster.ExecutionContext(),
        hello_world,
        environment=create_num_csv_environment(),
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }
