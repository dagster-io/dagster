import logging

from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.execution.context.logger import InitLoggerContext
from dagster._core.log_manager import DagsterLogManager
from dagster._utils.log import construct_single_handler_logger


class LogTestHandler(logging.Handler):
    def __init__(self, records):
        self.records = records
        super().__init__()

    def emit(self, record):
        self.records.append(record)


def test_log_level_filtering():
    records = []
    critical_records = []

    debug_logger_def = construct_single_handler_logger(
        "debug_handler", "debug", LogTestHandler(records)
    )
    critical_logger_def = construct_single_handler_logger(
        "critical_handler", "critical", LogTestHandler(critical_records)
    )

    loggers = [
        logger_def.logger_fn(
            InitLoggerContext(
                {},
                logger_def,
                job_def=GraphDefinition(node_defs=[], name="test").to_job(),
                run_id="",
            )
        )
        for logger_def in [debug_logger_def, critical_logger_def]
    ]

    log_manager = DagsterLogManager.create(loggers=loggers)

    log_manager.debug("Hello, there!")

    messages = [x.dagster_meta["orig_message"] for x in records]

    assert "Hello, there!" in messages

    critical_messages = [x.dagster_meta["orig_message"] for x in critical_records]

    assert "Hello, there!" not in critical_messages
