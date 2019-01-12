import subprocess

from dagster import execute_pipeline
from dagster.tutorials.intro_tutorial.execution_context import (
    define_execution_context_pipeline_step_one,
    define_execution_context_pipeline_step_two,
    define_execution_context_pipeline_step_three,
)
from dagster.utils import script_relative_path


def test_execution_context():
    for pipeline_definition in [
        define_execution_context_pipeline_step_one,
        define_execution_context_pipeline_step_two,
        define_execution_context_pipeline_step_three,
    ]:
        pipeline = pipeline_definition()
        execute_pipeline(pipeline, {'context': {'default': {'config': {'log_level': 'DEBUG'}}}})


def test_execution_context_invocation_as_script():
    subprocess.check_output(
        [
            'python',
            script_relative_path('../../../dagster/tutorials/intro_tutorial/execution_context.py'),
        ]
    )
