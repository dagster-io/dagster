# isort: skip_file
from dagster import pipeline, solid

# start_custom_file_output_log


@solid
def file_log_solid(context):
    context.log.info("Hello world!")


@pipeline
def file_log_pipeline():
    file_log_solid()


# end_custom_file_output_log
