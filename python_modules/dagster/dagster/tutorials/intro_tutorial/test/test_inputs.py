import pytest

from dagster import PipelineConfigEvaluationError, execute_pipeline
from dagster.tutorials.utils import check_cli_execute_file_pipeline
from dagster.utils import script_relative_path

from ..inputs import (
    execute_with_another_world,
    define_hello_typed_inputs_pipeline,
)


def test_hello_inputs_parameterized_pipeline():
    result = execute_with_another_world()
    assert result.success
    solid_result = result.result_for_solid('add_hello_to_word')
    assert solid_result.transformed_value() == 'Hello, Mars!'


def test_hello_inputs_parameterized_cli_pipeline():
    check_cli_execute_file_pipeline(
        script_relative_path('../inputs.py'),
        'define_hello_inputs_pipeline',
        script_relative_path('../inputs_env.yml'),
    )


def test_hello_typed_inputs():
    with pytest.raises(PipelineConfigEvaluationError):
        execute_pipeline(
            define_hello_typed_inputs_pipeline(),
            {'solids': {'add_hello_to_word': {'inputs': {'word': 343}}}},
        )
