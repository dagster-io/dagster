import pytest

from dagster import execute_pipeline, PipelineConfigEvaluationError
from dagster.tutorials.intro_tutorial.configuration_schemas import (
    define_demo_configuration_schema_pipeline,
    define_demo_configuration_schema_repo,
    define_typed_demo_configuration_schema_pipeline,
)
from dagster.utils import script_relative_path
from dagster.utils.yaml_utils import load_yaml_from_path
from dagster.core.errors import DagsterExecutionStepExecutionError


def intro_tutorial_path(path):
    return script_relative_path('../../../dagster/tutorials/intro_tutorial/{}'.format(path))


def test_demo_configuration_schema_pipeline_correct_yaml():
    result = execute_pipeline(
        define_demo_configuration_schema_pipeline(),
        load_yaml_from_path(intro_tutorial_path('configuration_schemas.yml')),
    )
    assert result.success
    assert len(result.solid_result_list) == 2
    count_letters_result = result.result_for_solid('count_letters').transformed_value()
    expected_value = {'q': 2, 'u': 4, 'x': 2}
    assert set(count_letters_result.keys()) == set(expected_value.keys())
    for key, value in expected_value.items():
        assert count_letters_result[key] == value
    assert result.result_for_solid('multiply_the_word').transformed_value() == 'quuxquux'


def test_demo_configuration_schema_pipeline_runtime_error():
    with pytest.raises(DagsterExecutionStepExecutionError) as e_info:
        execute_pipeline(
            define_demo_configuration_schema_pipeline(),
            load_yaml_from_path(intro_tutorial_path('configuration_schemas_runtime_error.yml')),
        )

    assert isinstance(e_info.value.__cause__, TypeError)


def test_demo_configuration_schema_pipeline_wrong_field():
    with pytest.raises(
        PipelineConfigEvaluationError,
        match=('Undefined field "multiply_the_word_with_typed_config" at path ' 'root:solids'),
    ):
        execute_pipeline(
            define_demo_configuration_schema_pipeline(),
            load_yaml_from_path(intro_tutorial_path('configuration_schemas_wrong_field.yml')),
        )


def test_typed_demo_configuration_schema_pipeline_correct_yaml():
    result = execute_pipeline(
        define_typed_demo_configuration_schema_pipeline(),
        load_yaml_from_path(intro_tutorial_path('configuration_schemas_typed.yml')),
    )
    assert result.success
    assert len(result.solid_result_list) == 2
    count_letters_result = result.result_for_solid('count_letters').transformed_value()
    expected_value = {'q': 2, 'u': 4, 'x': 2}
    assert set(count_letters_result.keys()) == set(expected_value.keys())
    for key, value in expected_value.items():
        assert count_letters_result[key] == value
    assert result.result_for_solid('typed_multiply_the_word').transformed_value() == 'quuxquux'


def test_typed_demo_configuration_schema_type_mismatch_error():
    with pytest.raises(
        PipelineConfigEvaluationError,
        match=(
            'Type failure at path "root:solids:typed_multiply_the_word:config:factor" on type '
            '"Int"'
        ),
    ):
        execute_pipeline(
            define_typed_demo_configuration_schema_pipeline(),
            load_yaml_from_path(
                script_relative_path(
                    (
                        '../../../dagster/tutorials/intro_tutorial/'
                        'configuration_schemas_type_mismatch_error.yml'
                    )
                )
            ),
        )


def test_configuration_schema_repository():
    repo = define_demo_configuration_schema_repo()
    assert repo
    assert repo.get_all_pipelines()
