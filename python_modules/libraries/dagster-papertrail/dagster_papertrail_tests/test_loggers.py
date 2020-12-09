import logging

from dagster import ModeDefinition, execute_pipeline, pipeline, solid
from dagster.loggers import colored_console_logger
from dagster.seven import mock
from dagster_papertrail import papertrail_logger


@solid
def hello_logs(context):
    context.log.info("Hello, world!")


@pipeline(
    mode_defs=[
        ModeDefinition(
            logger_defs={"console": colored_console_logger, "papertrail": papertrail_logger}
        )
    ]
)
def hello_pipeline():
    hello_logs()


def test_papertrail_logger():
    with mock.patch("logging.handlers.SysLogHandler.emit") as emit:

        result = execute_pipeline(
            hello_pipeline,
            {
                "loggers": {
                    "console": {"config": {"log_level": "INFO"}},
                    "papertrail": {
                        "config": {
                            "log_level": "INFO",
                            "name": "hello_pipeline",
                            "papertrail_address": "127.0.0.1",
                            "papertrail_port": 12345,
                        }
                    },
                }
            },
        )

    log_record = emit.call_args_list[0][0][0]

    assert isinstance(log_record, logging.LogRecord)
    assert log_record.name == "hello_pipeline"
    assert log_record.levelname == "INFO"

    assert log_record.msg == "system - {run_id} - hello_logs - Hello, world!".format(
        run_id=result.run_id
    )
