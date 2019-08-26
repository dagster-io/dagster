from dagster import execute_pipeline, lambda_solid, pipeline


@lambda_solid
def hello_world():
    return 'hello'


@pipeline
def hello_world_pipeline():
    hello_world()


if __name__ == '__main__':
    result = execute_pipeline(hello_world_pipeline)
    assert result.success
