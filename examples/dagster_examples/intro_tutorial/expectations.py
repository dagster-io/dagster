from dagster import (
    ExpectationDefinition,
    ExpectationResult,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
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


def define_expectations_tutorial_pipeline():
    return PipelineDefinition(name='expectations_tutorial_pipeline', solids=[add_ints])
