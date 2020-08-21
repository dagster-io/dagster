from dagster import pipeline, solid


@solid
def hello_logs(context):
    context.log.info("Hello, world!")


@pipeline
def demo_pipeline():
    hello_logs()
