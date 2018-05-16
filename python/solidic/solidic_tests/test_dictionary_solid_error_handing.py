import pytest

import check

from solidic.definitions import (SolidInputDefinition, SolidOutputDefinition)

from solidic.execution import (
    materialize_input, SolidExecutionError, execute_core_transform, execute_output,
    SolidExecutionContext
)


def create_test_context():
    return SolidExecutionContext()


def test_basic_input_error_handling():
    def input_fn_inst(_context, _arg_dict):
        raise Exception('a user error')

    erroring_input = SolidInputDefinition(
        name='some_input', input_fn=input_fn_inst, argument_def_dict={}
    )

    with pytest.raises(SolidExecutionError):
        materialize_input(create_test_context(), erroring_input, {})


def test_basic_core_transform_error_handling():
    def transform_fn(an_input):
        check.str_param(an_input, 'an_input')
        raise Exception('exception during core transform')

    with pytest.raises(SolidExecutionError):
        execute_core_transform(
            create_test_context(),
            transform_fn, {'an_input': 'value'},
            transform_requires_context=False
        )


def test_basic_output_transform_error_handling():
    def output_fn_inst(_data, arg_dict):
        assert arg_dict == {}
        raise Exception('error during output')

    output_def = SolidOutputDefinition(
        name='CUSTOM', output_fn=output_fn_inst, argument_def_dict={}
    )

    with pytest.raises(SolidExecutionError):
        execute_output(
            create_test_context(), output_def, output_arg_dict={}, materialized_output='whatever'
        )
