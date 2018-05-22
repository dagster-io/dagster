import pytest

from dagster.solidic.definitions import (
    SolidExpectationDefinition,
    SolidExpectationResult,
)
from dagster.solidic.execution import (
    _execute_output_expectation, SolidUserCodeExecutionError, SolidExecutionContext
)


def create_test_context():
    return SolidExecutionContext()


def test_basic_failing_output_expectation():
    def failing(_output):
        return SolidExpectationResult(
            success=False,
            message='some message',
        )

    result = _execute_output_expectation(
        create_test_context(), SolidExpectationDefinition('failing', failing), 'not used'
    )

    assert isinstance(result, SolidExpectationResult)
    assert not result.success
    assert result.message == 'some message'


def test_basic_passing_output_expectation():
    def success(_output):
        return SolidExpectationResult(
            success=True,
            message='yay',
        )

    expectation = SolidExpectationDefinition('success', success)
    result = _execute_output_expectation(create_test_context(), expectation, 'not used')

    assert isinstance(result, SolidExpectationResult)
    assert result.success
    assert result.message == 'yay'


def test_output_expectation_user_error():
    def throwing(_output):
        raise Exception('user error')

    with pytest.raises(SolidUserCodeExecutionError):
        _execute_output_expectation(
            create_test_context(), SolidExpectationDefinition('throwing', throwing), 'not used'
        )
