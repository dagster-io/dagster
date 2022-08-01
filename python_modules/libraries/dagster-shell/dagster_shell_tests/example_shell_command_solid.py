# pylint: disable=no-value-for-parameter
from dagster_shell.solids import create_shell_command_solid

from dagster._legacy import pipeline


@pipeline
def pipe():
    a = create_shell_command_solid('echo "hello, world!"', name="a")
    a()
