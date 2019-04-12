from collections import defaultdict

from dagster import (
    Any,
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    Int,
    PipelineDefinition,
    RepositoryDefinition,
    String,
    lambda_solid,
    solid,
)


@solid(inputs=[InputDefinition('word', String)], config_field=Field(Any))
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@solid(inputs=[InputDefinition('word', String)], config_field=Field(Dict({'factor': Field(Int)})))
def typed_multiply_the_word(context, word):
    return word * context.solid_config['factor']


@solid(
    inputs=[InputDefinition('word', String)], config_field=Field(Dict({'factor': Field(String)}))
)
def typed_multiply_the_word_error(context, word):
    return word * context.solid_config['factor']


def define_demo_configuration_schema_pipeline():
    return PipelineDefinition(
        name='demo_configuration_schema',
        solids=[multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('multiply_the_word')}},
    )


def define_typed_demo_configuration_schema_pipeline():
    return PipelineDefinition(
        name='typed_demo_configuration_schema',
        solids=[typed_multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('typed_multiply_the_word')}},
    )


def define_typed_demo_configuration_schema_error_pipeline():
    return PipelineDefinition(
        name='typed_demo_configuration_schema_error',
        solids=[typed_multiply_the_word_error, count_letters],
        dependencies={
            'count_letters': {'word': DependencyDefinition('typed_multiply_the_word_error')}
        },
    )


def define_demo_configuration_schema_repo():
    return RepositoryDefinition(
        name='demo_configuration_schema_repo',
        pipeline_dict={
            'demo_configuration_schema': define_demo_configuration_schema_pipeline,
            'typed_demo_configuration_schema': define_typed_demo_configuration_schema_pipeline,
            'typed_demo_configuration_schema_error': define_typed_demo_configuration_schema_error_pipeline,
        },
    )
