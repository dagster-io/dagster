from dagster import PipelineDefinition, execute_pipeline, lambda_solid


@lambda_solid
def hello_world():
    return 'hello'


def define_hello_world_pipeline():
    return PipelineDefinition(name='hello_world_pipeline', solids=[hello_world])


if __name__ == '__main__':
    result = execute_pipeline(define_hello_world_pipeline())
    assert result.success
