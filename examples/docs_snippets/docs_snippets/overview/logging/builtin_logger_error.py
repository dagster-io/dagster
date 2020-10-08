from dagster import pipeline, solid


# start_builtin_logger_error_marker_0
@solid
def hello_logs_error(context):
    raise Exception("Somebody set up us the bomb")


@pipeline
def demo_pipeline_error():
    hello_logs_error()


# end_builtin_logger_error_marker_0
