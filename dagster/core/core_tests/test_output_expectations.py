import pytest

from dagster.core.definitions import (
    ExpectationDefinition,
    ExpectationResult,
)
from dagster.core.execution import (
    _execute_output_expectation, DagsterUserCodeExecutionError, DagsterExecutionContext
)


def create_test_context():
    return DagsterExecutionContext()


def test_basic_failing_output_expectation():
    def failing(_output):
        return ExpectationResult(
            success=False,
            message='some message',
        )

    result = _execute_output_expectation(
        create_test_context(), ExpectationDefinition('failing', failing), 'not used'
    )

    assert isinstance(result, ExpectationResult)
    assert not result.success
    assert result.message == 'some message'


def test_basic_passing_output_expectation():
    def success(_output):
        return ExpectationResult(
            success=True,
            message='yay',
        )

    expectation = ExpectationDefinition('success', success)
    result = _execute_output_expectation(create_test_context(), expectation, 'not used')

    assert isinstance(result, ExpectationResult)
    assert result.success
    assert result.message == 'yay'


def test_output_expectation_user_error():
    def throwing(_output):
        raise Exception('user error')

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_output_expectation(
            create_test_context(), ExpectationDefinition('throwing', throwing), 'not used'
        )
