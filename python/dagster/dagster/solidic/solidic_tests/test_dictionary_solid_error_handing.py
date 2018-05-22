import pytest

from dagster import check

from dagster.solidic.definitions import (SolidInputDefinition, SolidOutputDefinition)

from dagster.solidic.execution import (
    _execute_input, SolidUserCodeExecutionError, _execute_core_transform, _execute_output,
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

    with pytest.raises(SolidUserCodeExecutionError):
        _execute_input(create_test_context(), erroring_input, {})


def test_basic_core_transform_error_handling():
    def transform_fn(an_input):
        check.str_param(an_input, 'an_input')
        raise Exception('exception during core transform')

    with pytest.raises(SolidUserCodeExecutionError):
        _execute_core_transform(
            create_test_context(),
            transform_fn,
            {'an_input': 'value'},
        )


def test_basic_output_transform_error_handling():
    def output_fn_inst(_data, arg_dict):
        assert arg_dict == {}
        raise Exception('error during output')

    output_def = SolidOutputDefinition(
        name='CUSTOM', output_fn=output_fn_inst, argument_def_dict={}
    )

    with pytest.raises(SolidUserCodeExecutionError):
        _execute_output(
            create_test_context(), output_def, output_arg_dict={}, materialized_output='whatever'
        )
