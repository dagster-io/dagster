from collections import defaultdict

from dagster import (
    Field,
    PipelineDefinition,
    DependencyDefinition,
    InputDefinition,
    solid,
    types,
    lambda_solid,
)


@solid(config_field=Field(types.Dict({'word': Field(types.String)})))
def double_the_word(info):
    return info.config['word'] * 2


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_part_eight_step_one_pipeline():
    return PipelineDefinition(
        name='part_eight_step_one_pipeline',
        solids=[double_the_word, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('double_the_word'),
            },
        },
    )
