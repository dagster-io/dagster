from dagster import file_relative_path, pipeline
from dagster_shell import create_shell_script_solid


@pipeline
def pipe():
    a = create_shell_script_solid(file_relative_path(__file__, "hello_world.sh"), name="a")
    a()
