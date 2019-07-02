from collections import defaultdict

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    String,
    lambda_solid,
    solid,
)

from dagster_aws.s3.resources import s3_resource
from dagster_aws.s3.system_storage import s3_plus_default_storage_defs


@solid(input_defs=[InputDefinition('word', String)], config={'factor': Field(Int)})
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@lambda_solid(input_defs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@lambda_solid()
def error_solid():
    raise Exception('Unusual error')


def define_demo_execution_pipeline():
    return PipelineDefinition(
        name='demo_pipeline',
        solid_defs=[multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('multiply_the_word')}},
        mode_defs=[
            ModeDefinition(
                system_storage_defs=s3_plus_default_storage_defs, resource_defs={'s3': s3_resource}
            )
        ],
    )


def define_demo_error_pipeline():
    return PipelineDefinition(name='demo_error_pipeline', solid_defs=[error_solid])


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo',
        pipeline_dict={
            'demo_pipeline': define_demo_execution_pipeline,
            'demo_error_pipeline': define_demo_error_pipeline,
        },
    )
