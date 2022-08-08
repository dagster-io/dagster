# isort: skip_file
from dagster._legacy import pipeline, solid

# start_custom_file_output_log


@op
def file_log_op(context):
    context.log.info("Hello world!")


@pipeline
def file_log_pipeline():
    file_log_op()


# end_custom_file_output_log
