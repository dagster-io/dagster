from dagster import (
    DependencyDefinition,
    InputDefinition,
    Int,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    lambda_solid,
)


@lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
def add_one(num):
    return num + 1


@lambda_solid(inputs=[InputDefinition('num', Int)], output=OutputDefinition(Int))
def mult_two(num):
    return num * 2


def define_pandas_hello_world():
    return PipelineDefinition(
        name='math',
        solids=[add_one, mult_two],
        dependencies={'add_one': {}, 'mult_two': {'num': DependencyDefinition(add_one.name)}},
    )


def define_repository():
    return RepositoryDefinition(name='test', pipeline_dict={'math': define_pandas_hello_world})
