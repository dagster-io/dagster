import os

import pandas as pd

import check

from solidic.execution import (materialize_input, execute_solid, SolidExecutionContext)
from solidic.types import SolidPath
from solidic.definitions import (Solid, SolidOutputTypeDefinition)
from solidic_pandas.definitions import create_solid_pandas_csv_input

from .test_utils import (script_relative_path, get_temp_file_name)


def create_test_context():
    return SolidExecutionContext()


def test_pandas_input():
    csv_input = create_solid_pandas_csv_input(name='num_csv')
    df = materialize_input(
        create_test_context(), csv_input, {'path': script_relative_path('num.csv')}
    )

    assert isinstance(df, pd.DataFrame)
    assert df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4]}


def test_pandas_solid():
    csv_input = create_solid_pandas_csv_input(name='num_csv')

    def transform(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    test_output = {}

    def output_fn_inst(df, _output_arg_dict):
        assert isinstance(df, pd.DataFrame)
        test_output['df'] = df

    custom_output_type_def = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=output_fn_inst,
        argument_def_dict={},
    )

    single_solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output_type_defs=[custom_output_type_def],
    )

    execute_solid(
        create_test_context(),
        single_solid,
        input_arg_dicts={'num_csv': {
            'path': script_relative_path('num.csv')
        }},
        output_type='CUSTOM',
        output_arg_dict={},
    )

    assert test_output['df'].to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}


def test_pandas_csv_to_csv():
    csv_input = create_solid_pandas_csv_input(name='num_csv')

    def transform(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    def output_fn_inst(df, output_arg_dict):
        path = check.str_elem(output_arg_dict, 'path')
        df.to_csv(path, index=False)

    csv_output_type_def = SolidOutputTypeDefinition(
        name='CSV', output_fn=output_fn_inst, argument_def_dict={'path': SolidPath}
    )

    solid = Solid(
        name='sum_table',
        inputs=[csv_input],
        transform_fn=transform,
        output_type_defs=[csv_output_type_def],
    )

    with get_temp_file_name() as temp_file_name:
        result = execute_solid(
            create_test_context(),
            solid,
            input_arg_dicts={'num_csv': {
                'path': script_relative_path('num.csv')
            }},
            output_type='CSV',
            output_arg_dict={'path': temp_file_name},
        )

        assert result.success

        output_df = pd.read_csv(temp_file_name)
        assert output_df.to_dict('list') == {'num1': [1, 3], 'num2': [2, 4], 'sum': [3, 7]}
