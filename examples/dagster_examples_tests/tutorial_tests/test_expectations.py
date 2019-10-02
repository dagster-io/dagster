from dagster_examples.intro_tutorial.expectations import expectations_tutorial_pipeline

from dagster import execute_pipeline


def test_intro_tutorial_expectations_step_one():
    result = execute_pipeline(
        expectations_tutorial_pipeline,
        {
            'loggers': {'console': {'config': {'log_level': 'DEBUG'}}},
            'solids': {'add_ints': {'inputs': {'num_one': {'value': 2}, 'num_two': {'value': 3}}}},
        },
    )

    assert result.success


def define_failing_environment_config():
    return {
        'loggers': {'console': {'config': {'log_level': 'DEBUG'}}},
        'solids': {'add_ints': {'inputs': {'num_one': {'value': -2}, 'num_two': {'value': 3}}}},
    }


def test_intro_tutorial_expectations_step_two():
    result = execute_pipeline(expectations_tutorial_pipeline, define_failing_environment_config())

    assert result.success
