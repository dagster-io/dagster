import pytest

from dagster.core.definitions import (
    SolidInputDefinition, SolidExpectationDefinition, SolidExpectationResult
)
from dagster.core.execution import (
    _execute_input_expectation, SolidUserCodeExecutionError, DagsterExecutionContext
)
from dagster.core.types import SolidString


def create_test_context():
    return DagsterExecutionContext()


def test_basic_failing_input_expectation():
    def failing_expectation(_some_input):
        return SolidExpectationResult(success=False, message='Some failure')

    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString},
        expectations=[
            SolidExpectationDefinition(name='failing', expectation_fn=failing_expectation)
        ]
    )

    result = _execute_input_expectation(
        create_test_context(), some_input.expectations[0], 'some_value'
    )

    assert isinstance(result, SolidExpectationResult)
    assert not result.success
    assert result.message == 'Some failure'


def test_basic_passing_input_expectation():
    def passing_expectation(_some_input):
        return SolidExpectationResult(success=True, message='yayayaya')

    some_input = SolidInputDefinition(
        name='some_input',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString},
        expectations=[
            SolidExpectationDefinition(name='passing', expectation_fn=passing_expectation)
        ]
    )

    result = _execute_input_expectation(
        create_test_context(), some_input.expectations[0], 'some_value'
    )

    assert isinstance(result, SolidExpectationResult)
    assert result.success
    assert result.message == 'yayayaya'


def test_input_expectation_user_error():
    def throwing(_something):
        raise Exception('nope')

    failing_during_expectation_input = SolidInputDefinition(
        name='failing_during_expectation',
        input_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': SolidString},
        expectations=[
            SolidExpectationDefinition(name='passing', expectation_fn=throwing)
        ]
    )

    with pytest.raises(SolidUserCodeExecutionError):
        _execute_input_expectation(
            create_test_context(), failing_during_expectation_input.expectations[0], 'some_value'
        )
