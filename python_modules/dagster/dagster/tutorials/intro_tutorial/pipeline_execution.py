from collections import defaultdict

from dagster import (
    DependencyDefinition,
    Dict,
    Field,
    InputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    String,
    lambda_solid,
    solid,
)


@solid(config_field=Field(Dict({'word': Field(String)})))
def double_the_word(info):
    return info.config['word'] * 2


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_demo_execution_pipeline():
    return PipelineDefinition(
        name='demo_execution',
        solids=[double_the_word, count_letters],
        dependencies={
            'count_letters': {'word': DependencyDefinition('double_the_word')}
        },
    )


def define_demo_execution_repo():
    return RepositoryDefinition(
        name='demo_execution_repo',
        pipeline_dict={'part_seven': define_demo_execution_pipeline},
    )
