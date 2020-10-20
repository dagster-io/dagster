from dagster import pipeline
from dagster_shell import create_shell_command_solid


@pipeline
def pipe():
    a = create_shell_command_solid('echo "hello, world!"', name="a")
    a()
