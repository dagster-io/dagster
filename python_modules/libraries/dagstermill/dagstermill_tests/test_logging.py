import json
import logging
import os

from dagster import (
    ModeDefinition,
    String,
    execute_pipeline,
    local_file_manager,
    logger,
    pipeline,
    reconstructable,
    seven,
)
from dagster.core.test_utils import instance_for_test
from dagster.utils import safe_tempfile_path
from dagstermill.examples.repository import hello_logging


class LogTestFileHandler(logging.Handler):
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.isfile(self.file_path):
            with open(self.file_path, "a"):  # Create file if does not exist
                pass
        super(LogTestFileHandler, self).__init__()

    def emit(self, record):
        with open(self.file_path, "a") as fd:
            fd.write(seven.json.dumps(record.__dict__) + "\n")


@logger(config_schema={"name": String, "log_level": String, "file_path": String})
def test_file_logger(init_context):
    klass = logging.getLoggerClass()
    logger_ = klass(
        init_context.logger_config["name"], level=init_context.logger_config["log_level"]
    )
    handler = LogTestFileHandler(init_context.logger_config["file_path"])
    logger_.addHandler(handler)
    handler.setLevel(init_context.logger_config["log_level"])
    return logger_


@pipeline(
    mode_defs=[
        ModeDefinition(
            logger_defs={
                "test": test_file_logger,
                "critical": test_file_logger,
            },
            resource_defs={
                "file_manager": local_file_manager,
            },
        )
    ]
)
def hello_logging_pipeline():
    hello_logging()


def test_logging():
    with safe_tempfile_path() as test_file_path:
        with safe_tempfile_path() as critical_file_path:
            with instance_for_test() as instance:
                execute_pipeline(
                    reconstructable(hello_logging_pipeline),
                    {
                        "loggers": {
                            "test": {
                                "config": {
                                    "name": "test",
                                    "file_path": test_file_path,
                                    "log_level": "DEBUG",
                                }
                            },
                            "critical": {
                                "config": {
                                    "name": "critical",
                                    "file_path": critical_file_path,
                                    "log_level": "CRITICAL",
                                }
                            },
                        }
                    },
                    instance=instance,
                )

                with open(test_file_path, "r") as test_file:
                    records = [
                        json.loads(line)
                        for line in test_file.read().strip("\n").split("\n")
                        if line
                    ]

                with open(critical_file_path, "r") as critical_file:
                    critical_records = [
                        json.loads(line)
                        for line in critical_file.read().strip("\n").split("\n")
                        if line
                    ]

    messages = [x["dagster_meta"]["orig_message"] for x in records]

    assert "Hello, there!" in messages

    critical_messages = [x["dagster_meta"]["orig_message"] for x in critical_records]

    assert "Hello, there!" not in critical_messages
