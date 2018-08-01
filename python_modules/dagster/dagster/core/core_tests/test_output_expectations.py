import pytest

import dagster
from dagster.core.definitions import (
    ExpectationDefinition,
    ExpectationResult,
)
from dagster.core.execution import (
    _execute_output_expectation, DagsterUserCodeExecutionError, ExecutionContext
)


def create_test_context():
    return ExecutionContext()


def create_dummy_output_info(expect_def):
    return dagster.OutputExpectationInfo(
        solid=dagster.SolidDefinition(
            name='dummy',
            inputs=[],
            transform_fn=lambda _context, _args: None,
            output=dagster.OutputDefinition(expectations=[expect_def])
        ),
        expectation_def=expect_def
    )


def test_basic_failing_output_expectation():
    def failing(_context, _info, _output):
        return ExpectationResult(
            success=False,
            message='some message',
        )

    result = _execute_output_expectation(
        create_test_context(), create_dummy_output_info(ExpectationDefinition('failing', failing)),
        'not used'
    )

    assert isinstance(result, ExpectationResult)
    assert not result.success
    assert result.message == 'some message'


def test_basic_passing_output_expectation():
    def success(_context, _info, _output):
        return ExpectationResult(
            success=True,
            message='yay',
        )

    expectation = ExpectationDefinition('success', success)
    result = _execute_output_expectation(
        create_test_context(),
        create_dummy_output_info(expectation),
        'not used',
    )

    assert isinstance(result, ExpectationResult)
    assert result.success
    assert result.message == 'yay'


def test_output_expectation_user_error():
    def throwing(_output):
        raise Exception('user error')

    with pytest.raises(DagsterUserCodeExecutionError):
        _execute_output_expectation(
            create_test_context(),
            create_dummy_output_info(ExpectationDefinition('throwing', throwing)), 'not used'
        )
