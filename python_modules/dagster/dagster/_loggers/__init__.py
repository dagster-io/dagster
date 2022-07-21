import logging
from typing import TYPE_CHECKING, Mapping, Sequence, Tuple

import coloredlogs

from dagster import _seven
from dagster._config import Field
from dagster._core.definitions.logger_definition import LoggerDefinition, logger
from dagster._core.utils import coerce_valid_log_level
from dagster._utils.log import default_date_format_string, default_format_string

if TYPE_CHECKING:
    from dagster._core.execution.context.logger import InitLoggerContext


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
    level = coerce_valid_log_level(init_context.logger_config["log_level"])
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)
    coloredlogs.install(
        logger=logger_,
        level=level,
        fmt=default_format_string(),
        datefmt=default_date_format_string(),
        field_styles={"levelname": {"color": "blue"}, "asctime": {"color": "green"}},
        level_styles={"debug": {}, "error": {"color": "red"}},
    )
    return logger_


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

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            return _seven.json.dumps(record.__dict__)

    handler.setFormatter(JsonFormatter())
    logger_.addHandler(handler)

    return logger_


def default_system_loggers() -> Sequence[Tuple["LoggerDefinition", Mapping[str, object]]]:
    """If users don't provide configuration for any loggers, we instantiate these loggers with the
    default config.

    Returns:
        List[Tuple[LoggerDefinition, dict]]: Default loggers and their associated configs."""
    return [(colored_console_logger, {"name": "dagster", "log_level": "DEBUG"})]


def default_loggers() -> Mapping[str, "LoggerDefinition"]:
    return {"console": colored_console_logger}
