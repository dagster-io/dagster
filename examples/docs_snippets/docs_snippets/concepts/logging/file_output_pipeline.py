# isort: skip_file
from dagster import job, op

# start_custom_file_output_log


@op
def file_log_op(context):
    context.log.info("Hello world!")


@job
def file_log_job():
    file_log_op()


# end_custom_file_output_log
