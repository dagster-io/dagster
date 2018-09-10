# pylint: disable=W0622,W0614,W0401
from collections import defaultdict
import pytest

from dagster import *

from dagster.utils import script_relative_path


@solid(config_def=ConfigDefinition(types.ConfigDictionary({'word': Field(types.String)})))
def double_the_word_with_typed_config(_context, conf):
    return conf['word'] * 2


@solid(
    config_def=ConfigDefinition(types.ConfigDictionary({
        'word': Field(types.String)
    })),
    outputs=[OutputDefinition(types.String)],
)
def typed_double_word(_context, conf):
    return conf['word'] * 2


@solid(
    config_def=ConfigDefinition(types.ConfigDictionary({
        'word': Field(types.String)
    })),
    outputs=[OutputDefinition(types.Int)],
)
def typed_double_word_mismatch(_context, conf):
    return conf['word'] * 2


@lambda_solid(inputs=[InputDefinition('word')])
def count_letters(word):
    counts = defaultdict(int)
    for letter in word:
        counts[letter] += 1
    return dict(counts)


def define_part_eight_step_one_pipeline():
    return PipelineDefinition(
        name='part_eight_step_one',
        solids=[double_the_word_with_typed_config, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('double_the_word_with_typed_config'),
            },
        },
    )


def define_part_eight_step_two_pipeline():
    return PipelineDefinition(
        name='part_eight_step_two',
        solids=[typed_double_word, count_letters],
        dependencies={
            'count_letters': {
                'word': DependencyDefinition('typed_double_word'),
            },
        },
    )


def define_part_eight_step_three_pipeline():
    return PipelineDefinition(
        name='part_eight_step_three',
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
    environment = config.load_environment(script_relative_path('env_step_one_works.yml'))

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
    environment = config.load_environment(script_relative_path('env_step_one_type_error.yml'))
    with pytest.raises(DagsterTypeError, match='Expected valid value for String'):
        execute_pipeline(define_part_eight_step_one_pipeline(), environment)


def test_part_eight_repo_step_one_wrong_field():
    environment = config.load_environment(script_relative_path('env_step_one_field_error.yml'))

    with pytest.raises(DagsterTypeError, match='Field wrong_word not found'):
        execute_pipeline(define_part_eight_step_one_pipeline(), environment)


def test_part_eight_repo_step_two():
    environment = config.load_environment(script_relative_path('env_step_two_works.yml'))

    pipeline_result = execute_pipeline(define_part_eight_step_two_pipeline(), environment)

    assert pipeline_result.success
    assert pipeline_result.result_for_solid('typed_double_word').transformed_value() == 'baazbaaz'


def test_part_eight_repo_step_three():
    environment = config.load_environment(script_relative_path('env_step_three_type_mismatch.yml'))

    with pytest.raises(
        DagsterInvariantViolationError,
        match='Solid typed_double_word_mismatch output name result output quuxquux'
    ):
        execute_pipeline(define_part_eight_step_three_pipeline(), environment)
