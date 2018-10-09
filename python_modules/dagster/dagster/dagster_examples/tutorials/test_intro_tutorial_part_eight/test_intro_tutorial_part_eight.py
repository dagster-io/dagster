# pylint: disable=W0622,W0614,W0401
from collections import defaultdict
import pytest

from dagster import (
    ConfigDefinition,
    DagsterInvariantViolationError,
    DagsterTypeError,
    DependencyDefinition,
    Field,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    RepositoryDefinition,
    config,
    execute_pipeline,
    lambda_solid,
    solid,
    types,
)

from dagster.utils import (
    load_yaml_from_path,
    script_relative_path,
)

name = 'WordConfig'
fields = {'word': Field(types.String)}
WordConfig = types.ConfigDictionary(name=name, fields=fields)


@solid(config_def=ConfigDefinition(WordConfig))
def double_the_word_with_typed_config(info):
    return info.config['word'] * 2


@solid(
    config_def=ConfigDefinition(WordConfig),
    outputs=[OutputDefinition(types.String)],
)
def typed_double_word(info):
    return info.config['word'] * 2


@solid(
    config_def=ConfigDefinition(WordConfig),
    outputs=[OutputDefinition(types.Int)],
)
def typed_double_word_mismatch(info):
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
        solids=[double_the_word_with_typed_config, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('double_the_word_with_typed_config'),
            },
        },
    )


def define_part_eight_step_two_pipeline():
    return PipelineDefinition(
        name='part_eight_step_two_pipeline',
        solids=[typed_double_word, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('typed_double_word'),
            },
        },
    )


def define_part_eight_step_three_pipeline():
    return PipelineDefinition(
        name='part_eight_step_three_pipeline',
        solids=[typed_double_word_mismatch, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('typed_double_word_mismatch'),
            },
        },
    )


def define_part_eight_repo():
    return RepositoryDefinition(
        name='part_eight_repo',
        pipeline_dict={
            'part_eight_step_one': define_part_eight_step_one_pipeline,
            'part_eight_step_two': define_part_eight_step_two_pipeline,
            'part_eight_step_three': define_part_eight_step_three_pipeline,
        }
    )


def test_part_eight_repo_step_one():
    environment = load_yaml_from_path(script_relative_path('env_step_one_works.yml'))

    pipeline_result = execute_pipeline(define_part_eight_step_one_pipeline(), environment)

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('double_the_word_with_typed_config'
                                            ).transformed_value() == 'quuxquux'
    assert pipeline_result.result_for_solid('count_letters').transformed_value() == {
        'q': 2,
        'u': 4,
        'x': 2,
    }


def test_part_eight_repo_step_one_wrong_env():
    environment = load_yaml_from_path(script_relative_path('env_step_one_type_error.yml'))
    with pytest.raises(DagsterTypeError, match='Expected valid value for String'):
        execute_pipeline(define_part_eight_step_one_pipeline(), environment)


def test_part_eight_repo_step_one_wrong_field():
    environment = load_yaml_from_path(script_relative_path('env_step_one_field_error.yml'))

    with pytest.raises(DagsterTypeError, match='Field wrong_word not found'):
        execute_pipeline(define_part_eight_step_one_pipeline(), environment)


def test_part_eight_repo_step_two():
    environment = load_yaml_from_path(script_relative_path('env_step_two_works.yml'))

    pipeline_result = execute_pipeline(define_part_eight_step_two_pipeline(), environment)

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('typed_double_word').transformed_value() == 'baazbaaz'


def test_part_eight_repo_step_three():
    environment = load_yaml_from_path(script_relative_path('env_step_three_type_mismatch.yml'))

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Solid typed_double_word_mismatch output name result output quuxquux'
    ):
        execute_pipeline(define_part_eight_step_three_pipeline(), environment)
