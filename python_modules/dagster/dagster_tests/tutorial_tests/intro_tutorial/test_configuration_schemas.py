import pytest

from dagster import DagsterInvariantViolationError, execute_pipeline, PipelineConfigEvaluationError
from dagster.tutorials.intro_tutorial.configuration_schemas import (
    define_demo_configuration_schema_pipeline,
    define_typed_demo_configuration_schema_pipeline,
    define_typed_demo_configuration_schema_error_pipeline,
)
from dagster.utils import script_relative_path
from dagster.utils.yaml_utils import load_yaml_from_path


def test_demo_configuration_schema_pipeline_correct_yaml():
    result = execute_pipeline(
        define_demo_configuration_schema_pipeline(),
        load_yaml_from_path(
            script_relative_path(
                '../../../dagster/tutorials/intro_tutorial/configuration_schemas.yml'
            )
        ),
    )
    assert result.success
    assert len(result.result_list) == 2
    count_letters_result = result.result_for_solid('count_letters').transformed_value()
    expected_value = {'q': 2, 'u': 4, 'x': 2}
    assert set(count_letters_result.keys()) == set(expected_value.keys())
    for key, value in expected_value.items():
        assert count_letters_result[key] == value
    assert result.result_for_solid('double_the_word').transformed_value() == 'quuxquux'


def test_demo_configuration_schema_pipeline_bad_yaml_1():
    with pytest.raises(
        PipelineConfigEvaluationError,
        match=(
            'Type failure at path "root:solids:double_the_word:config:word" ' 'on type "String".'
        ),
    ):
        execute_pipeline(
            define_demo_configuration_schema_pipeline(),
            load_yaml_from_path(
                script_relative_path(
                    '../../../dagster/tutorials/intro_tutorial/configuration_schemas_error_1.yml'
                )
            ),
        )


def test_demo_configuration_schema_pipeline_bad_yaml_2():
    with pytest.raises(
        PipelineConfigEvaluationError,
        match=('Undefined field "double_the_word_with_typed_config" at path ' 'root:solids'),
    ):
        execute_pipeline(
            define_demo_configuration_schema_pipeline(),
            load_yaml_from_path(
                script_relative_path(
                    '../../../dagster/tutorials/intro_tutorial/configuration_schemas_error_2.yml'
                )
            ),
        )


def test_typed_demo_configuration_schema_pipeline_correct_yaml():
    result = execute_pipeline(
        define_typed_demo_configuration_schema_pipeline(),
        load_yaml_from_path(
            script_relative_path(
                '../../../dagster/tutorials/intro_tutorial/configuration_schemas_typed.yml'
            )
        ),
    )
    assert result.success
    assert len(result.result_list) == 2
    count_letters_result = result.result_for_solid('count_letters').transformed_value()
    expected_value = {'q': 2, 'u': 4, 'x': 2}
    assert set(count_letters_result.keys()) == set(expected_value.keys())
    for key, value in expected_value.items():
        assert count_letters_result[key] == value
    assert result.result_for_solid('typed_double_the_word').transformed_value() == 'quuxquux'


def test_typed_demo_configuration_schema_error_pipeline_correct_yaml():
    with pytest.raises(
        DagsterInvariantViolationError,
        match='type failure: Expected valid value for Int but got \'quuxquux\'',
    ):
        execute_pipeline(
            define_typed_demo_configuration_schema_error_pipeline(),
            load_yaml_from_path(
                script_relative_path(
                    '../../../dagster/tutorials/intro_tutorial/configuration_schemas_typed_error.yml'
                )
            ),
        )
