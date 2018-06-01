import pytest

from dagster.core.definitions import (
    ExpectationDefinition, ExpectationResult, create_single_source_input
)
from dagster.core.execution import (
    _execute_input_expectation, DagsterUserCodeExecutionError, DagsterExecutionContext
)
from dagster.core import types


def create_test_context():
    return DagsterExecutionContext()


def test_basic_failing_input_expectation():
    def failing_expectation(_some_input):
        return ExpectationResult(success=False, message='Some failure')

    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': types.STRING},
        expectations=[
            ExpectationDefinition(name='failing', expectation_fn=failing_expectation)
        ]
    )

    result = _execute_input_expectation(
        create_test_context(), some_input.expectations[0], 'some_value'
    )

    assert isinstance(result, ExpectationResult)
    assert not result.success
    assert result.message == 'Some failure'


def test_basic_passing_input_expectation():
    def passing_expectation(_some_input):
        return ExpectationResult(success=True, message='yayayaya')

    some_input = create_single_source_input(
        name='some_input',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': types.STRING},
        expectations=[
            ExpectationDefinition(name='passing', expectation_fn=passing_expectation)
        ]
    )

    result = _execute_input_expectation(
        create_test_context(), some_input.expectations[0], 'some_value'
    )

    assert isinstance(result, ExpectationResult)
    assert result.success
    assert result.message == 'yayayaya'


def test_input_expectation_user_error():
    def throwing(_something):
        raise Exception('nope')

    failing_during_expectation_input = create_single_source_input(
        name='failing_during_expectation',
        source_fn=lambda arg_dict: [{'key': arg_dict['str_arg']}],
        argument_def_dict={'str_arg': types.STRING},
        expectations=[
            ExpectationDefinition(name='passing', expectation_fn=throwing)
        ]
    )

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_input_expectation(
            create_test_context(), failing_during_expectation_input.expectations[0], 'some_value'
        )
