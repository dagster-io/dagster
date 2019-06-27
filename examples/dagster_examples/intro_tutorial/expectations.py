from dagster import (
    lambda_solid,
    pipeline,
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    Int,
    OutputDefinition,
)


@lambda_solid(
    inputs=[
        InputDefinition(
            'num_one',
            Int,
            expectations=[
                ExpectationDefinition(
                    name='check_positive',
                    expectation_fn=lambda _info, value: ExpectationResult(success=value > 0),
                )
            ],
        ),
        InputDefinition('num_two', Int),
    ],
    output=OutputDefinition(Int),
)
def add_ints(num_one, num_two):
    return num_one + num_two


@pipeline
def expectations_tutorial_pipeline():
    add_ints()  # pylint: disable=no-value-for-parameter
