import pandas as pd

# from solidic.definitions import (Solid, SolidOutputTypeDefinition, SolidInputDefinition)
from solidic.execution import (SolidExecutionContext, execute_solid, output_solid)
from solidic_utils.test import (script_relative_path, get_temp_file_name)

import solidic_pandas as solidic_pd


def create_test_context():
    return SolidExecutionContext()


def test_hello_world_no_library_support():
    csv_input = solidic_pd.csv_input('num_csv')

    def transform_fn(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    # supports CSV and PARQUET by default
    hello_world = solidic_pd.dataframe_solid(
        name='hello_world', inputs=[csv_input], transform_fn=transform_fn
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}
    result = execute_solid(create_test_context(), hello_world, input_arg_dicts)

    assert result.success

    assert result.materialized_output.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }

    with get_temp_file_name() as temp_file_name:
        output_result = output_solid(
            create_test_context(), hello_world, input_arg_dicts, 'CSV', {'path': temp_file_name}
        )

        assert output_result.success

        assert pd.read_csv(temp_file_name).to_dict('list') == {
            'num1': [1, 3],
            'num2': [2, 4],
            'sum': [3, 7],
        }
