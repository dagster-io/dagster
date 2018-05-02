import pytest

from solidic.definitions import (
    SolidOutputTypeDefinition,
    SolidExpectationDefinition,
    SolidExpectationResult,
)
from solidic.execution import (
    evaluate_output_expectation, SolidExecutionError, SolidExecutionContext
)
from solidic.types import SolidString


def create_test_context():
    return SolidExecutionContext()


def test_basic_failing_output_expectation():
    def failing(_output):
        return SolidExpectationResult(
            success=False,
            message='some message',
        )

    output_type = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=lambda output: output,
        argument_def_dict={},
        expectations=[SolidExpectationDefinition('failing', failing)],
    )

    result = evaluate_output_expectation(
        create_test_context(), output_type.expectations[0], 'not used'
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

    output_type = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=lambda output: output,
        argument_def_dict={},
        expectations=[SolidExpectationDefinition('success', success)],
    )

    result = evaluate_output_expectation(
        create_test_context(), output_type.expectations[0], 'not used'
    )

    assert isinstance(result, SolidExpectationResult)
    assert result.success
    assert result.message == 'yay'


def test_output_expectation_user_error():
    def throwing(_output):
        raise Exception('user error')

    output_type = SolidOutputTypeDefinition(
        name='CUSTOM',
        output_fn=lambda output: output,
        argument_def_dict={},
        expectations=[SolidExpectationDefinition('throwing', throwing)],
    )

    with pytest.raises(SolidExecutionError):
        evaluate_output_expectation(create_test_context(), output_type.expectations[0], 'not used')
