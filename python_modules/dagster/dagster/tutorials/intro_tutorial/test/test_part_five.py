import pytest

from dagster import execute_pipeline

from ..part_five import (
    define_execution_context_pipeline_step_one,
    define_execution_context_pipeline_step_two,
    define_execution_context_pipeline_step_three,
)


def test_tutorial_part_five():
    for pipeline_definition in [
        define_execution_context_pipeline_step_one,
        define_execution_context_pipeline_step_two,
        define_execution_context_pipeline_step_three,
    ]:
        pipeline = pipeline_definition()

        with pytest.raises(Exception):
            execute_pipeline(
                pipeline,
                {'context': {'default': {'config': {'log_level': 'DEBUG'}}}},
            )
