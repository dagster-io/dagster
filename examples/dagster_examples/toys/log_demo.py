from dagster import PipelineDefinition, solid


@solid
def hello_logs(context):
    context.log.info('Hello, world!')


@solid
def hello_error(context):
    raise Exception('Somebody set up us the bomb')


def define_hello_logs_pipeline():
    return PipelineDefinition(name='hello_logs', solid_defs=[hello_logs])


def define_hello_error_pipeline():
    return PipelineDefinition(name='hello_error', solid_defs=[hello_error])
