from dagster import (
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    lambda_solid,
)


@lambda_solid(output=OutputDefinition())
def solid_one():
    return 'foo'


@lambda_solid(inputs=[InputDefinition('arg_one')], output=OutputDefinition())
def solid_two(arg_one):
    return arg_one * 2


def define_hello_dag_pipeline():
    return PipelineDefinition(
        name='hello_dag_pipeline',
        solids=[solid_one, solid_two],
        dependencies={'solid_two': {'arg_one': DependencyDefinition('solid_one')}},
    )
