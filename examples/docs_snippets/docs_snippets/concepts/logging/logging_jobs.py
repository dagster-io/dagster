from dagster_aws.cloudwatch.loggers import cloudwatch_logger

from dagster import graph, op, repository
from dagster._loggers import colored_console_logger


# start_logging_mode_marker_0
@op
def log_op(context):
    context.log.info("Hello, world!")


@graph
def hello_logs():
    log_op()


local_logs = hello_logs.to_job(
    name="local_logs", logger_defs={"console": colored_console_logger}
)
prod_logs = hello_logs.to_job(
    name="prod_logs", logger_defs={"cloudwatch": cloudwatch_logger}
)

# end_logging_mode_marker_0


@repository
def logs_repo():
    return [local_logs, prod_logs]
