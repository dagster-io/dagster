from collections import defaultdict

from dagster import (
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


@solid(inputs=[InputDefinition('word', String)], config_field=Field(Dict({'factor': Field(Int)})))
def multiply_the_word(context, word):
    return word * context.solid_config['factor']


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_demo_execution_pipeline():
    return PipelineDefinition(
        name='demo_pipeline',
        solids=[multiply_the_word, count_letters],
        dependencies={'count_letters': {'word': DependencyDefinition('multiply_the_word')}},
    )


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo', pipeline_dict={'demo_pipeline': define_demo_execution_pipeline}
    )
