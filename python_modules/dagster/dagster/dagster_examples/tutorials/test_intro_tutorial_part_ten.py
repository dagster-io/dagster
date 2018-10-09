# pylint: disable=W0622,W0614,W0401
from logging import DEBUG

import pytest

from dagster import (
    ConfigDefinition,
    DagsterExpectationFailedError,
    DependencyDefinition,
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    config,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)


@solid(
    config_def=ConfigDefinition(types.Int),
    outputs=[
        OutputDefinition(
            types.Int,
            expectations=[
                ExpectationDefinition(
                    name="check_positive",
                    expectation_fn=lambda _info, value: ExpectationResult(success=value > 0)
                )
            ]
        )
    ],
)
def injest_a(info):
    return info.config


@solid(
    config_def=ConfigDefinition(types.Int),
    outputs=[OutputDefinition(types.Int)],
)
def injest_b(info):
    return info.config


@lambda_solid(
    inputs=[InputDefinition('num_one', types.Int),
            InputDefinition('num_two', types.Int)],
    output=OutputDefinition(types.Int),
)
def add_ints(num_one, num_two):
    return num_one + num_two


def define_part_ten_step_one_pipeline():
    return PipelineDefinition(
        name='part_ten_step_one_pipeline',
        solids=[injest_a, injest_b, add_ints],
        dependencies={
            'add_ints': {
                'num_one': DependencyDefinition('injest_a'),
                'num_two': DependencyDefinition('injest_b'),
            },
        },
    )


def test_intro_tutorial_part_ten_step_one():
    result = execute_pipeline(
        define_part_ten_step_one_pipeline(),
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'injest_a': {
                    'config': 2,
                },
                'injest_b': {
                    'config': 3,
                },
            }
        },
    )

    assert result.success


def define_failing_environment_config():
    return {
        'context': {
            'default': {
                'config': {
                    'log_level': 'DEBUG',
                }
            }
        },
        'solids': {
            'injest_a': {
                'config': -2,
            },
            'injest_b': {
                'config': 3,
            },
        }
    }


def test_intro_tutorial_part_ten_step_two_fails_hard():
    with pytest.raises(DagsterExpectationFailedError):
        execute_pipeline(
            define_part_ten_step_one_pipeline(),
            define_failing_environment_config(),
        )


def test_intro_tutorial_part_ten_step_two_fails_soft():
    result = execute_pipeline(
        define_part_ten_step_one_pipeline(),
        define_failing_environment_config(),
        throw_on_error=False,
    )

    assert not result.success


if __name__ == '__main__':
    execute_pipeline(
        define_part_ten_step_one_pipeline(),
        {
            'context': {
                'default': {
                    'config': {
                        'log_level': 'DEBUG',
                    }
                }
            },
            'solids': {
                'injest_a': {
                    'config': -2,
                },
                'injest_b': {
                    'config': 3,
                },
            },
            'expectations': {
                'evaluate': True,
            },
        },
    )
