# pylint: disable=no-value-for-parameter
from dagster_shell import create_shell_script_op

from dagster import file_relative_path, graph


@graph
def my_graph():
    a = create_shell_script_op(file_relative_path(__file__, "hello_world.sh"), name="a")
    a()
