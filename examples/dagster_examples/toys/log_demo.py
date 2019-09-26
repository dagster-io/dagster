from dagster import pipeline, solid


@solid
def hello_logs(context):
    context.log.info('Hello, world!')


@solid
def hello_error(context):
    raise Exception('Somebody set up us the bomb')


@pipeline
def hello_logs_pipeline():
    hello_logs()


@pipeline
def hello_error_pipeline():
    hello_error()
