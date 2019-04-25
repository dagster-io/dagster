from dagster import (
    PipelineDefinition,
    execute_pipeline,
    solid,
    OutputDefinition,
    ExpectationDefinition,
    Any,
    ExpectationResult,
    InputDefinition,
)


@solid(
    inputs=[
        InputDefinition(
            "df",
            dagster_type=Any,
            expectations=[
                ExpectationDefinition(
                    "bob", lambda _info, value: ExpectationResult(success=value > 0)
                )
            ],
        )
    ],
    outputs=[OutputDefinition()],
    description="Tranform the dataframe to prepare for machine learning.",
)
def transformations(context, df):
    context.log.info("This doesn't do anything yet")
    return df


def test_expectations_crash_repro():
    pipeline_def = PipelineDefinition(name='expectations_crash', solids=[transformations])
    assert pipeline_def

    execute_pipeline(
        pipeline_def,
        environment_dict={'solids': {'transformations': {'inputs': {'df': {'value': 2}}}}},
    )
