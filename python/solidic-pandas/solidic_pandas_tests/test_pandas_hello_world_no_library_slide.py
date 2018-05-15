import pandas as pd

import solidic
from solidic.definitions import (Solid, SolidOutputDefinition, SolidInputDefinition)
from solidic.execution import (SolidExecutionContext, execute_solid)
from solidic_utils.test import (script_relative_path)


def create_test_context():
    return SolidExecutionContext()


def test_hello_world_no_library_support():
    csv_input = SolidInputDefinition(
        name='num_csv',
        input_fn=lambda context, arg_dict: pd.read_csv(arg_dict['path']),
        argument_def_dict={'path': solidic.PATH},
    )

    def transform_fn(num_csv):
        num_csv['sum'] = num_csv['num1'] + num_csv['num2']
        return num_csv

    csv_output = SolidOutputDefinition(
        name='CSV',
        output_fn=lambda df, context, arg_dict: df.to_csv(arg_dict['path'], index=False),
        argument_def_dict={'path': solidic.PATH}
    )

    hello_world = Solid(
        name='hello_world',
        inputs=[csv_input],
        transform_fn=transform_fn,
        outputs=[csv_output],
    )

    input_arg_dicts = {'num_csv': {'path': script_relative_path('num.csv')}}
    result = execute_solid(create_test_context(), hello_world, input_arg_dicts)

    assert result.success

    assert result.materialized_output.to_dict('list') == {
        'num1': [1, 3],
        'num2': [2, 4],
        'sum': [3, 7],
    }
