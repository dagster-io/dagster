import pytest

from dagster import DagsterExpectationFailedError, execute_pipeline, RunConfig
from dagster.tutorials.intro_tutorial.expectations import define_expectations_tutorial_pipeline


def test_intro_tutorial_expectations_step_one():
    result = execute_pipeline(
        define_expectations_tutorial_pipeline(),
        {
            'context': {'default': {'config': {'log_level': 'DEBUG'}}},
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 3}}}},
        },
    )

    assert result.success


def define_failing_environment_config():
    return {
        'context': {'default': {'config': {'log_level': 'DEBUG'}}},
        'solids': {'add_ints': {'inputs': {'num_one': {'value': -2}, 'num_two': {'value': 3}}}},
    }


def test_intro_tutorial_expectations_step_two_fails_hard():
    with pytest.raises(DagsterExpectationFailedError):
        execute_pipeline(
            define_expectations_tutorial_pipeline(), define_failing_environment_config()
        )


def test_intro_tutorial_expectations_step_two_fails_soft():
    result = execute_pipeline(
        define_expectations_tutorial_pipeline(),
        define_failing_environment_config(),
        run_config=RunConfig.nonthrowing_in_process(),
    )

    assert not result.success
