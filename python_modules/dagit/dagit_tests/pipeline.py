from dagster import (
    InputDefinition,
    Int,
    OutputDefinition,
    RepositoryDefinition,
    lambda_solid,
    pipeline,
)


@lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
def add_one(num):
    return num + 1


@lambda_solid(input_defs=[InputDefinition('num', Int)], output_def=OutputDefinition(Int))
def mult_two(num):
    return num * 2


@pipeline
def math():
    return mult_two(num=add_one())


def define_repository():
    return RepositoryDefinition(name='test', pipeline_defs=[math])
