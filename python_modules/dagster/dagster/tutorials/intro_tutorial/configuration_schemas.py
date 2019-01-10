from collections import defaultdict

from dagster import (
    DependencyDefinition,
    InputDefinition,
    lambda_solid,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    solid,
    types,
)


@solid(
    config_field=types.Field(types.Dict({'word': types.Field(types.String)}))
)
def double_the_word(info):
    return info.config['word'] * 2


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


@solid(
    config_field=types.Field(types.Dict({'word': types.Field(types.String)})),
    outputs=[OutputDefinition(types.String)],
)
def typed_double_the_word(info):
    return info.config['word'] * 2


@solid(
    config_field=types.Field(types.Dict({'word': types.Field(types.String)})),
    outputs=[OutputDefinition(types.Int)],
)
def typed_double_the_word_error(info):
    return info.config['word'] * 2


def define_demo_configuration_schema_pipeline():
    return PipelineDefinition(
        name='demo_configuration_schema',
        solids=[double_the_word, count_letters],
        dependencies={
            'count_letters': {'word': DependencyDefinition('double_the_word')}
        },
    )


def define_typed_demo_configuration_schema_pipeline():
    return PipelineDefinition(
        name='typed_demo_configuration_schema',
        solids=[typed_double_the_word, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('typed_double_the_word')
            }
        },
    )


def define_typed_demo_configuration_schema_error_pipeline():
    return PipelineDefinition(
        name='typed_demo_configuration_schema_error',
        solids=[typed_double_the_word_error, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('typed_double_the_word_error')
            }
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
