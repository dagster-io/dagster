import pandas as pd

from dagster.execution import (materialize_input, execute_solid)
from solidic.definitions import (SolidExecutionContext, Solid, SolidOutputTypeDefinition)
from dagster.solid_pandas_defs import create_solid_pandas_csv_input


def script_relative_path(file_path):
    import check
    import inspect
    import os
    check.str_param(file_path, 'file_path')
    scriptdir = inspect.stack()[1][1]
    return os.path.join(os.path.dirname(os.path.abspath(scriptdir)), file_path)


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
