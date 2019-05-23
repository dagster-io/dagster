import subprocess

from dagster import execute_pipeline
from dagster_examples.intro_tutorial.execution_context import define_execution_context_pipeline
from dagster.utils import script_relative_path


def test_execution_context():
    pipeline = define_execution_context_pipeline()
    execute_pipeline(pipeline, {'loggers': {'console': {'config': {'log_level': 'DEBUG'}}}})


def test_execution_context_invocation_as_script():
    subprocess.check_output(
        [
            'python',
            script_relative_path(
                '../../../../../examples/dagster_examples/intro_tutorial/execution_context.py'
            ),
        ]
    )
