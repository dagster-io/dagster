from dagster import ModeDefinition, pipeline, solid
from dagster.loggers import colored_console_logger
from dagster_aws.cloudwatch.loggers import cloudwatch_logger


# start_logging_mode_marker_0
@solid
def hello_logs(context):
    context.log.info("Hello, world!")


@pipeline(
    mode_defs=[
        ModeDefinition(name="local", logger_defs={"console": colored_console_logger}),
        ModeDefinition(name="prod", logger_defs={"cloudwatch": cloudwatch_logger}),
    ]
)
def hello_modes():
    hello_logs()


# end_logging_mode_marker_0
