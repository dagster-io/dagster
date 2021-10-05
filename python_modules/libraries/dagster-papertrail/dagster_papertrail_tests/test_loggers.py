import logging
from unittest import mock

from dagster import job, op
from dagster.loggers import colored_console_logger
from dagster_papertrail import papertrail_logger


@op
def hello_logs(context):
    context.log.info("Hello, world!")


@job(logger_defs={"console": colored_console_logger, "papertrail": papertrail_logger})
def do_logs():
    hello_logs()


def test_papertrail_logger():
    with mock.patch("logging.handlers.SysLogHandler.emit") as emit:
        result = do_logs.execute_in_process(
            run_config={
                "loggers": {
                    "console": {"config": {"log_level": "INFO"}},
                    "papertrail": {
                        "config": {
                            "log_level": "INFO",
                            "name": "do_logs",
                            "papertrail_address": "127.0.0.1",
                            "papertrail_port": 12345,
                        }
                    },
                }
            }
        )

    log_record = emit.call_args_list[0][0][0]

    assert isinstance(log_record, logging.LogRecord)
    assert log_record.name == "do_logs"
    assert log_record.levelname == "INFO"

    assert log_record.msg == "do_logs - {run_id} - hello_logs - Hello, world!".format(
        run_id=result.run_id
    )
