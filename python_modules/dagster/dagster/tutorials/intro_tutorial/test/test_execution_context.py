from dagster import execute_pipeline

from ..execution_context import (
    define_execution_context_pipeline_step_one,
    define_execution_context_pipeline_step_two,
    define_execution_context_pipeline_step_three,
)


def test_execution_context():
    for pipeline_definition in [
        define_execution_context_pipeline_step_one,
        define_execution_context_pipeline_step_two,
        define_execution_context_pipeline_step_three,
    ]:
        pipeline = pipeline_definition()
        execute_pipeline(
            pipeline,
            {'context': {'default': {'config': {'log_level': 'DEBUG'}}}},
        )
