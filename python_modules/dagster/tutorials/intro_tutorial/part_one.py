from dagster import (
    PipelineDefinition,
    lambda_solid,
)


@lambda_solid
def hello_world():
    return 'hello'


def define_hello_world_pipeline():
    return PipelineDefinition(
        name='part_one_pipeline',
        solids=[hello_world],
    )
