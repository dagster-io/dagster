# pylint: disable=no-value-for-parameter
from dagster import graph
from dagster_shell import create_shell_command_op


@graph
def my_graph():
    a = create_shell_command_op('echo "hello, world!"', name="a")
    a()
