from collections import defaultdict

from dagster import (
    DependencyDefinition,
    Field,
    InputDefinition,
    lambda_solid,
    PipelineDefinition,
    RepositoryDefinition,
    solid,
    types,
)


@solid(config_field=Field(types.Any))
def double_the_word(info):
    return info.config['word'] * 2


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_part_seven_pipeline():
    return PipelineDefinition(
        name='part_seven',
        solids=[double_the_word, count_letters],
        dependencies={
            'count_letters': {'word': DependencyDefinition('double_the_word')}
        },
    )


def define_part_seven_repo():
    return RepositoryDefinition(
        name='part_seven_repo',
        pipeline_dict={'part_seven': define_part_seven_pipeline},
    )
