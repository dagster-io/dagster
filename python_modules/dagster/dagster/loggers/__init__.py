import logging

import coloredlogs
from dagster import seven
from dagster.config import Field
from dagster.core.definitions.logger import logger
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils.log import default_format_string


@logger(
    {
        "log_level": Field(str, is_required=False, default_value="INFO"),
        "name": Field(str, is_required=False, default_value="dagster"),
    },
    description="The default colored console logger.",
)
def colored_console_logger(init_context):
    level = coerce_valid_log_level(init_context.logger_config["log_level"])
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)
    coloredlogs.install(
        logger=logger_,
        level=level,
        fmt=default_format_string(),
        field_styles={"levelname": {"color": "blue"}, "asctime": {"color": "green"}},
        level_styles={"debug": {}, "error": {"color": "red"}},
    )
    return logger_


@logger(
    {
        "log_level": Field(str, is_required=False, default_value="INFO"),
        "name": Field(str, is_required=False, default_value="dagster"),
    },
    description="A JSON-formatted console logger",
)
def json_console_logger(init_context):
    level = coerce_valid_log_level(init_context.logger_config["log_level"])
    name = init_context.logger_config["name"]

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    handler = coloredlogs.StandardErrorHandler()

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            return seven.json.dumps(record.__dict__)

    handler.setFormatter(JsonFormatter())
    logger_.addHandler(handler)

    return logger_


def default_system_loggers():
    """If users don't provide configuration for any loggers, we instantiate these loggers with the
    default config.

    Returns:
        List[Tuple[LoggerDefinition, dict]]: Default loggers and their associated configs."""
    return [(colored_console_logger, {"name": "dagster", "log_level": "DEBUG"})]


def default_loggers():
    return {"console": colored_console_logger}
