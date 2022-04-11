# pylint: disable=no-value-for-parameter
from dagster_shell import create_shell_command_op

from dagster import graph


@graph
def my_graph():
    a = create_shell_command_op('echo "hello, world!"', name="a")
    a()
