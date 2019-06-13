import collections

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    Int,
    PipelineDefinition,
    String,
    lambda_solid,
    solid,
)


@solid(inputs=[InputDefinition('word', String)], config={'factor': Field(Int)})
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    return collections.Counter(word)


def define_configuration_schema_pipeline():
    return PipelineDefinition(
        name='configuration_schema_pipeline',
        solids=[multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('multiply_the_word')}},
    )
