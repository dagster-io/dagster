import logging
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Optional, Tuple  # noqa: F401, UP035

import coloredlogs
from dagster_shared import seven

from dagster._config import Field
from dagster._core.definitions.logger_definition import LoggerDefinition, logger
from dagster._core.log_manager import (
    LOG_RECORD_EVENT_ATTR,
    LOG_RECORD_METADATA_ATTR,
    DagsterLogRecordMetadata,
)
from dagster._core.utils import coerce_valid_log_level
from dagster._serdes import pack_value
from dagster._utils.log import create_console_logger

if TYPE_CHECKING:
    from dagster._core.execution.context.logger import InitLoggerContext
    from dagster._core.instance import DagsterInstance


@logger(
    Field(
        {
            "log_level": Field(
                str,
                is_required=False,
                default_value="INFO",
                description="The logger's threshold.",
            ),
            "name": Field(
                str,
                is_required=False,
                default_value="dagster",
                description="The name of your logger.",
            ),
        },
        description="The default colored console logger.",
    ),
    description="The default colored console logger.",
)
def colored_console_logger(init_context: "InitLoggerContext") -> logging.Logger:
    """This logger provides support for sending Dagster logs to stdout in a colored format. It is
    included by default on jobs which do not otherwise specify loggers.
    """
    return create_console_logger(
        name=init_context.logger_config["name"],
        level=coerce_valid_log_level(init_context.logger_config["log_level"]),
    )


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        dict_to_dump = {}
        for k, v in record.__dict__.items():
            if k == LOG_RECORD_EVENT_ATTR:
                # Redundant with the "dagster_event" field under "dagster_meta"
                continue
            elif k == LOG_RECORD_METADATA_ATTR:
                # Events objects are not always JSON-serializable, so need to pack them first
                json_serializable_event = pack_value(v[LOG_RECORD_EVENT_ATTR])
                json_serializable_dagster_meta = DagsterLogRecordMetadata(
                    **{**v, "dagster_event": json_serializable_event}
                )
                dict_to_dump[LOG_RECORD_METADATA_ATTR] = json_serializable_dagster_meta
            else:
                dict_to_dump[k] = v

        return seven.json.dumps(dict_to_dump)


@logger(
    Field(
        {
            "log_level": Field(
                str,
                is_required=False,
                default_value="INFO",
                description="The logger's threshold.",
            ),
            "name": Field(
                str,
                is_required=False,
                default_value="dagster",
                description="The name of your logger.",
            ),
        },
        description="A JSON-formatted console logger.",
    ),
    description="A JSON-formatted console logger.",
)
def json_console_logger(init_context: "InitLoggerContext") -> logging.Logger:
    """This logger provides support for sending Dagster logs to stdout in json format.

    Example:
        .. code-block:: python

            from dagster import op, job
            from dagster.loggers import json_console_logger

            @op
            def hello_op(context):
                context.log.info('Hello, world!')
                context.log.error('This is an error')

            @job(logger_defs={'json_logger': json_console_logger})])
            def json_logged_job():
                hello_op()

    """
    level = coerce_valid_log_level(init_context.logger_config["log_level"])
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    handler = coloredlogs.StandardErrorHandler()

    handler.setFormatter(JsonLogFormatter())
    logger_.addHandler(handler)

    return logger_


def default_system_loggers(
    instance: Optional["DagsterInstance"],
) -> Sequence[tuple["LoggerDefinition", Mapping[str, object]]]:
    """If users don't provide configuration for any loggers, we instantiate these loggers with the
    default config.

    Returns:
        List[Tuple[LoggerDefinition, dict]]: Default loggers and their associated configs.
    """
    log_level = instance.python_log_level if (instance and instance.python_log_level) else "DEBUG"
    return [(colored_console_logger, {"name": "dagster", "log_level": log_level})]


def default_loggers() -> Mapping[str, "LoggerDefinition"]:
    return {"console": colored_console_logger}
