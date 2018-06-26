import pandas as pd

from dagster.core.execution import (
    DagsterExecutionContext, execute_single_solid, output_single_solid,
    create_single_solid_env_from_arg_dicts
)
from dagster.utils.test import (script_relative_path, get_temp_file_name)

import dagster.pandas_kernel as dagster_pd


def create_test_context():
    return DagsterExecutionContext()


def test_hello_world_no_library_support():
    csv_input = dagster_pd.dataframe_input('num_csv', sources=[dagster_pd.csv_dataframe_source()])

    def transform_fn(context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    hello_world = dagster_pd.dataframe_solid(
        name='hello_world', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}
    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_single_solid_env_from_arg_dicts(hello_world, input_arg_dicts)
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    with get_temp_file_name() as temp_file_name:
        output_result = output_single_solid(
            create_test_context(),
            hello_world,
            environment=create_single_solid_env_from_arg_dicts(hello_world, input_arg_dicts),
            materialization_type='CSV',
            arg_dict={'path': temp_file_name},
        )

        assert output_result.success

        assert pd.read_csv(temp_file_name).to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }


def test_hello_world_with_tables():
    table_input = dagster_pd.dataframe_input(
        'num_csv', sources=[dagster_pd.table_dataframe_source()]
    )

    def transform_fn(context, args):
        num_csv = args['num_csv']
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    # supports CSV and PARQUET by default
    hello_world = dagster_pd.dataframe_solid(
        name='hello_world', inputs=[table_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num_table.csv')}}
    result = execute_single_solid(
        create_test_context(),
        hello_world,
        environment=create_single_solid_env_from_arg_dicts(hello_world, input_arg_dicts)
    )

    assert result.success

    assert result.transformed_value.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    with get_temp_file_name() as temp_file_name:
        output_result = output_single_solid(
            create_test_context(),
            hello_world,
            environment=create_single_solid_env_from_arg_dicts(hello_world, input_arg_dicts),
            materialization_type='CSV',
            arg_dict={'path': temp_file_name},
        )

        assert output_result.success

        assert pd.read_csv(temp_file_name).to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }
