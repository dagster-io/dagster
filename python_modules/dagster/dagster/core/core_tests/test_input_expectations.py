import pytest

import dagster

from dagster.core.definitions import (
    ExpectationDefinition,
    ExpectationResult,
    ArgumentDefinition,
)
from dagster.core.execution import (
    _execute_input_expectation, DagsterUserCodeExecutionError, ExecutionContext
)
from dagster.core import types

from dagster.utils.compatability import create_custom_source_input


def create_test_context():
    return ExecutionContext()


def test_basic_failing_input_expectation():
    def failing_expectation(_context, _info, _some_input):
        return ExpectationResult(success=False, message='Some failure')

    some_input = create_custom_source_input(
        name='some_input',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': ArgumentDefinition(types.String)},
        expectations=[
            ExpectationDefinition(name='failing', expectation_fn=failing_expectation)
        ]
    )

    expectation_def = some_input.expectations[0]

    info = create_dummy_info(expectation_def)

    result = _execute_input_expectation(create_test_context(), info, 'some_value')

    assert isinstance(result, ExpectationResult)
    assert not result.success
    assert result.message == 'Some failure'


def create_dummy_info(expectation_def):
    info = dagster.InputExpectationInfo(
        solid=dagster.SolidDefinition(
            name='dummy',
            inputs=[],
            transform_fn=lambda _context, _args: None,
            output=dagster.OutputDefinition(),
        ),
        input_def=dagster.InputDefinition(name='dummy_input'),
        expectation_def=expectation_def,
    )
    return info


def test_basic_passing_input_expectation():
    def passing_expectation(_context, _info, _some_input):
        return ExpectationResult(success=True, message='yayayaya')

    some_input = create_custom_source_input(
        name='some_input',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': ArgumentDefinition(types.String)},
        expectations=[
            ExpectationDefinition(name='passing', expectation_fn=passing_expectation)
        ]
    )

    result = _execute_input_expectation(
        create_test_context(), create_dummy_info(some_input.expectations[0]), 'some_value'
    )

    assert isinstance(result, ExpectationResult)
    assert result.success
    assert result.message == 'yayayaya'


def test_input_expectation_user_error():
    def throwing(_context, _info, _something):
        raise Exception('nope')

    failing_during_expectation_input = create_custom_source_input(
        name='failing_during_expectation',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': ArgumentDefinition(types.String)},
        expectations=[
            ExpectationDefinition(name='passing', expectation_fn=throwing)
        ]
    )

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_input_expectation(
            create_test_context(),
            create_dummy_info(failing_during_expectation_input.expectations[0]),
            'some_value',
        )
