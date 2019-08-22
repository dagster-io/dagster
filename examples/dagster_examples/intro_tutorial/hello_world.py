# pylint: disable=no-value-for-parameter
from dagster import execute_pipeline, pipeline, solid


@solid
def hello_world(_):
    return 'hello'


@pipeline
def hello_world_pipeline():
    hello_world()


if __name__ == '__main__':
    result = execute_pipeline(hello_world_pipeline)
    assert result.success
