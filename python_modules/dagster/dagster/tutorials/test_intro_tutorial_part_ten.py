import pytest

from dagster import (
    DagsterExpectationFailedError,
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
)


@lambda_solid(
    inputs=[
        InputDefinition(
            'num_one',
            Int,
            expectations=[
                ExpectationDefinition(
                    name='check_positive',
                    expectation_fn=lambda _info, value: ExpectationResult(
                        success=value > 0
                    ),
                )
            ],
        ),
        InputDefinition('num_two', Int),
    ],
    output=OutputDefinition(Int),
)
def add_ints(num_one, num_two):
    return num_one + num_two


def define_expectations_tutorial_pipeline():
    return PipelineDefinition(
        name='part_ten_step_one_pipeline', solids=[add_ints]
    )


def test_intro_tutorial_part_ten_step_one():
    result = execute_pipeline(
        define_expectations_tutorial_pipeline(),
        {
            'context': {'default': {'config': {'log_level': 'DEBUG'}}},
            'solids': {
                'add_ints': {
                    'inputs': {
                        'num_one': {'value': 2},
                        'num_two': {'value': 3},
                    }
                }
            },
        },
    )

    assert result.success


def define_failing_environment_config():
    return {
        'context': {'default': {'config': {'log_level': 'DEBUG'}}},
        'solids': {
            'add_ints': {
                'inputs': {'num_one': {'value': -2}, 'num_two': {'value': 3}}
            }
        },
    }


def test_intro_tutorial_part_ten_step_two_fails_hard():
    with pytest.raises(DagsterExpectationFailedError):
        execute_pipeline(
            define_expectations_tutorial_pipeline(),
            define_failing_environment_config(),
        )


def test_intro_tutorial_part_ten_step_two_fails_soft():
    result = execute_pipeline(
        define_expectations_tutorial_pipeline(),
        define_failing_environment_config(),
        throw_on_error=False,
    )

    assert not result.success
