import json
import logging
import os

import pytest
from dagster import (
    String,
    _seven as seven,
    execute_job,
    job,
    logger,
    reconstructable,
)
from dagster._core.test_utils import instance_for_test
from dagster._utils import safe_tempfile_path
from dagstermill.examples.repository import hello_logging
from dagstermill.io_managers import (
    ConfigurableLocalOutputNotebookIOManager,
    local_output_notebook_io_manager,
)


class LogTestFileHandler(logging.Handler):
    def __init__(self, file_path):
        self.file_path = file_path
        if not os.path.isfile(self.file_path):
            with open(self.file_path, "a", encoding="utf8"):  # Create file if does not exist
                pass
        super().__init__()

    def emit(self, record):
        with open(self.file_path, "a", encoding="utf8") as fd:
            fd.write(
                seven.json.dumps({"the_message": record.__dict__["dagster_meta"]["orig_message"]})
                + "\n"
            )


@logger(config_schema={"name": String, "log_level": String, "file_path": String})
def test_file_logger(init_context):
    klass = logging.getLoggerClass()
    logger_ = klass(
        init_context.logger_config["name"],
        level=init_context.logger_config["log_level"],
    )
    handler = LogTestFileHandler(init_context.logger_config["file_path"])
    logger_.addHandler(handler)
    handler.setLevel(init_context.logger_config["log_level"])
    return logger_


@job(
    logger_defs={
        "test": test_file_logger,
        "critical": test_file_logger,
    },
    resource_defs={
        "output_notebook_io_manager": local_output_notebook_io_manager,
    },
)
def hello_logging_job():
    hello_logging()


@job(
    logger_defs={
        "test": test_file_logger,
        "critical": test_file_logger,
    },
    resource_defs={
        "output_notebook_io_manager": (
            ConfigurableLocalOutputNotebookIOManager.configure_at_launch()
        ),
    },
)
def hello_logging_job_pythonic():
    hello_logging()


@pytest.fixture(name="hello_logging_job_type", params=[True, False])
def hello_logging_job_type_fixture(request):
    if request.param:
        return hello_logging_job
    else:
        return hello_logging_job_pythonic


def test_logging(hello_logging_job_type) -> None:
    with safe_tempfile_path() as test_file_path:
        with safe_tempfile_path() as critical_file_path:
            with instance_for_test() as instance:
                execute_job(
                    reconstructable(hello_logging_job_type),
                    run_config={
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

                with open(test_file_path, encoding="utf8") as test_file:
                    records = [
                        json.loads(line)
                        for line in test_file.read().strip("\n").split("\n")
                        if line
                    ]

                with open(critical_file_path, encoding="utf8") as critical_file:
                    critical_records = [
                        json.loads(line)
                        for line in critical_file.read().strip("\n").split("\n")
                        if line
                    ]

    messages = [x["the_message"] for x in records]

    assert "Hello, there!" in messages

    critical_messages = [x["the_message"] for x in critical_records]

    assert "Hello, there!" not in critical_messages
