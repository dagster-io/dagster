from dagster_bash import bash_command_solid

from dagster import pipeline


@pipeline
def pipe():
    a = bash_command_solid('echo "hello, world!"', name='a')
    a()
