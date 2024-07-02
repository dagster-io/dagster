from dagster import graph, file_relative_path
from dagster_shell import create_shell_script_op


@graph
def my_graph():
    a = create_shell_script_op(file_relative_path(__file__, "hello_world.sh"), name="a")
    a()
