from dagster_shell import create_shell_command_solid

from dagster import pipeline


@pipeline
def pipe():
    a = create_shell_command_solid('echo "hello, world!"', name="a")
    a()
