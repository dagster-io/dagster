# pylint: disable=W0622,W0614,W0401
from collections import defaultdict

from dagster import *


@solid(
    config_def=ConfigDefinition(types.Any),
)
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
            'count_letters': {
                'word': DependencyDefinition('double_the_word'),
            },
        },
    )


def define_part_seven_repo():
    return RepositoryDefinition(
        name='part_seven_repo', pipeline_dict={
            'part_seven': define_part_seven_pipeline,
        }
    )


def test_part_seven_repo():
    environment = config.Environment(
        solids={
            'double_the_word': config.Solid(config={'word': 'bar'}),
        }
    )

    pipeline_result = execute_pipeline(define_part_seven_pipeline(), environment)

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('double_the_word').transformed_value() == 'barbar'
    assert pipeline_result.result_for_solid('count_letters').transformed_value() == {
        'b': 2,
        'a': 2,
        'r': 2,
    }
