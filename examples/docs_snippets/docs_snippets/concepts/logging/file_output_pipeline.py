"""isort:skip_file"""
from dagster import pipeline, solid


@solid
def file_log_solid(context):
    context.log.info("Hello world!")


@pipeline
def file_log_pipeline():
    file_log_solid()
