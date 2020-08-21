from dagster import pipeline, solid


@solid
def hello_logs_error(context):
    raise Exception("Somebody set up us the bomb")


@pipeline
def demo_pipeline_error():
    hello_logs_error()
