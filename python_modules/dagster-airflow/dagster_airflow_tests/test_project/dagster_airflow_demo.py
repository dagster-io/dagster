# pylint: disable=no-value-for-parameter, no-member
from collections import defaultdict

from dagster import (
    Field,
    InputDefinition,
    Int,
    ModeDefinition,
    Output,
    OutputDefinition,
    RepositoryDefinition,
    String,
    lambda_solid,
    pipeline,
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


@pipeline(
    mode_defs=[
        ModeDefinition(
            system_storage_defs=s3_plus_default_storage_defs, resource_defs={'s3': s3_resource}
        )
    ]
)
def demo_pipeline():
    count_letters(multiply_the_word())  # pylint: disable=no-value-for-parameter


@pipeline
def demo_error_pipeline():
    error_solid()


@solid(
    output_defs=[
        OutputDefinition(Int, 'out_1', is_optional=True),
        OutputDefinition(Int, 'out_2', is_optional=True),
        OutputDefinition(Int, 'out_3', is_optional=True),
    ]
)
def foo(_):
    yield Output(1, 'out_1')


@solid
def bar(_, input_arg):
    return input_arg


@pipeline
def optional_outputs():
    foo_res = foo()
    bar.alias('first_consumer')(input_arg=foo_res.out_1)
    bar.alias('second_consumer')(input_arg=foo_res.out_2)
    bar.alias('third_consumer')(input_arg=foo_res.out_3)


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo',
        pipeline_defs=[demo_pipeline, demo_error_pipeline, optional_outputs],
    )
