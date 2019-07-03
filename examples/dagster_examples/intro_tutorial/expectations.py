from dagster import (
    lambda_solid,
    pipeline,
    IOExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    Int,
    OutputDefinition,
)


@lambda_solid(
    input_defs=[
        InputDefinition(
            'num_one',
            Int,
            expectations=[
                IOExpectationDefinition(
                    name='check_positive',
                    expectation_fn=lambda _info, value: ExpectationResult(success=value > 0),
                )
            ],
        ),
        InputDefinition('num_two', Int),
    ],
    output_def=OutputDefinition(Int),
)
def add_ints(num_one, num_two):
    return num_one + num_two


@pipeline
def expectations_tutorial_pipeline():
    add_ints()  # pylint: disable=no-value-for-parameter
