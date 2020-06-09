from dagster_bash import create_bash_command_solid

from dagster import pipeline


@pipeline
def pipe():
    # create a new bash solid
    bash_solid = create_bash_command_solid('echo "hello, world!"', name='a')
    # invoke it
    bash_solid()
