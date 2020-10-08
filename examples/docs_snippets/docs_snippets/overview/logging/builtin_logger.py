from dagster import pipeline, solid


# start_builtin_logger_marker_0
@solid
def hello_logs(context):
    context.log.info("Hello, world!")


@pipeline
def demo_pipeline():
    hello_logs()


# end_builtin_logger_marker_0
