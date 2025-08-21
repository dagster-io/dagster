import copy
import logging
import logging.config
import sys
import traceback
import warnings
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Callable, NamedTuple, Optional, Union

import coloredlogs
import dagster_shared.seven as seven
from typing_extensions import TypeAlias

import dagster._check as check
from dagster._annotations import deprecated, public
from dagster._core.definitions.logger_definition import LoggerDefinition, logger
from dagster._core.utils import coerce_valid_log_level

if TYPE_CHECKING:
    import structlog

    from dagster._core.execution.context.logger import InitLoggerContext


class JsonFileHandler(logging.Handler):
    def __init__(self, json_path: str):
        super().__init__()
        self.json_path = check.str_param(json_path, "json_path")

    def emit(self, record: logging.LogRecord) -> None:
        from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR

        try:
            log_dict = copy.copy(record.__dict__)

            # This horrific monstrosity is to maintain backwards compatability
            # with the old behavior of the JsonFileHandler, which the clarify
            # project has a dependency on. It relied on the dagster-defined
            # properties smashing all the properties of the LogRecord object
            # and uploads all of those properties to a redshift table for
            # in order to do analytics on the log

            if LOG_RECORD_METADATA_ATTR in log_dict:
                dagster_meta_dict = log_dict[LOG_RECORD_METADATA_ATTR]
                del log_dict[LOG_RECORD_METADATA_ATTR]
            else:
                dagster_meta_dict = {}

            log_dict.update(dagster_meta_dict)

            with open(self.json_path, "a", encoding="utf8") as ff:
                text_line = seven.json.dumps(log_dict)
                ff.write(text_line + "\n")
        # Need to catch Exception here, so disabling lint
        except Exception as e:
            logging.critical("[%s] Error during logging!", self.__class__.__name__)
            logging.exception(str(e))


class StructuredLoggerMessage(
    NamedTuple(
        "_StructuredLoggerMessage",
        [
            ("name", str),
            ("message", str),
            ("level", int),
            ("meta", Mapping[str, object]),
            ("record", logging.LogRecord),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        message: str,
        level: int,
        meta: Mapping[str, object],
        record: logging.LogRecord,
    ):
        return super().__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(message, "message"),
            coerce_valid_log_level(level),
            check.mapping_param(meta, "meta"),
            check.inst_param(record, "record", logging.LogRecord),
        )


StructuredLoggerCallback: TypeAlias = Callable[[StructuredLoggerMessage], None]


class StructuredLoggerHandler(logging.Handler):
    def __init__(self, callback: StructuredLoggerCallback):
        super().__init__()
        self.callback = check.is_callable(callback, "callback")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.callback(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,  # type: ignore
                    record=record,
                )
            )
        # Need to catch Exception here, so disabling lint
        except Exception as e:
            logging.critical("[%s] Error during logging!", self.__class__.__name__)
            logging.exception(str(e))


def construct_single_handler_logger(
    name: str, level: Union[str, int], handler: logging.Handler
) -> LoggerDefinition:
    check.str_param(name, "name")
    check.inst_param(handler, "handler", logging.Handler)

    level = coerce_valid_log_level(level)

    @logger
    def single_handler_logger(_init_context: "InitLoggerContext"):
        klass = logging.getLoggerClass()
        logger_ = klass(name, level=level)
        logger_.addHandler(handler)
        handler.setLevel(level)
        return logger_

    return single_handler_logger


# Base python logger whose messages will be captured as structured Dagster log messages.
BASE_DAGSTER_LOGGER = logging.getLogger(name="dagster")


@public
def get_dagster_logger(name: Optional[str] = None) -> logging.Logger:
    """Creates a python logger whose output messages will be captured and converted into Dagster log
    messages. This means they will have structured information such as the step_key, run_id, etc.
    embedded into them, and will show up in the Dagster event log.

    This can be used as a more convenient alternative to `context.log` in most cases. If log level
    is not set explicitly, defaults to DEBUG.

    Args:
        name (Optional[str]): If supplied, will create a logger with the name "dagster.builtin.{name}",
            with properties inherited from the base Dagster logger. If omitted, the returned logger
            will be named "dagster.builtin".

    Returns:
        :class:`logging.Logger`: A logger whose output will be captured by Dagster.

    Example:
        .. code-block:: python

            from dagster import get_dagster_logger, op

            @op
            def hello_op():
                log = get_dagster_logger()
                for i in range(5):
                    # do something
                    log.info(f"Did {i+1} things!")

    """
    # enforce that the parent logger will always have a DEBUG log level
    BASE_DAGSTER_LOGGER.setLevel(logging.DEBUG)
    base_builtin = BASE_DAGSTER_LOGGER.getChild("builtin")
    if name:
        return base_builtin.getChild(name)
    return base_builtin


def define_structured_logger(
    name: str, callback: StructuredLoggerCallback, level: Union[str, int]
) -> LoggerDefinition:
    check.str_param(name, "name")
    check.callable_param(callback, "callback")
    level = coerce_valid_log_level(level)

    return construct_single_handler_logger(name, level, StructuredLoggerHandler(callback))


def define_json_file_logger(name: str, json_path: str, level: Union[str, int]) -> LoggerDefinition:
    check.str_param(name, "name")
    check.str_param(json_path, "json_path")
    level = coerce_valid_log_level(level)

    stream_handler = JsonFileHandler(json_path)
    stream_handler.setFormatter(define_default_formatter())
    return construct_single_handler_logger(name, level, stream_handler)


def get_stack_trace_array(exception: Exception) -> Sequence[str]:
    check.inst_param(exception, "exception", Exception)
    if hasattr(exception, "__traceback__"):
        tb = exception.__traceback__
    else:
        _exc_type, _exc_value, tb = sys.exc_info()
    return traceback.format_tb(tb)


def default_format_string() -> str:
    return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def default_date_format_string() -> str:
    return "%Y-%m-%d %H:%M:%S %z"


def define_default_formatter() -> logging.Formatter:
    return logging.Formatter(default_format_string(), default_date_format_string())


def get_structlog_shared_processors():
    # Deferred for import perf
    import structlog

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ExtraAdder(),
    ]

    return shared_processors


def get_structlog_json_formatter() -> "structlog.stdlib.ProcessorFormatter":
    # Deferred for import perf
    import structlog

    return structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=get_structlog_shared_processors(),
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )


@deprecated(
    breaking_version="2.0",
    subject="loggers.dagit",
    emit_runtime_warning=False,
)
def configure_loggers(
    handler: str = "default", formatter: str = "colored", log_level: Union[str, int] = "INFO"
) -> None:
    # Deferred for import perf
    import structlog

    # It's possible that structlog has already been configured by either the user or a controlling
    # process. If so, we don't want to override that configuration.
    if not structlog.is_configured():
        structlog.configure(
            processors=[
                *get_structlog_shared_processors(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
    json_formatter = get_structlog_json_formatter()

    LOGGING_CONFIG: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colored": {
                "()": coloredlogs.ColoredFormatter,
                "fmt": default_format_string(),
                "datefmt": default_date_format_string(),
                "field_styles": {"levelname": {"color": "blue"}, "asctime": {"color": "green"}},
                "level_styles": {"debug": {}, "error": {"color": "red"}},
            },
            "json": {
                "()": json_formatter.__class__,
                "foreign_pre_chain": json_formatter.foreign_pre_chain,
                "processors": json_formatter.processors,
            },
            "rich": {
                "()": structlog.stdlib.ProcessorFormatter,
                "foreign_pre_chain": get_structlog_shared_processors(),
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(),
                ],
            },
        },
        "handlers": {
            "default": {
                "formatter": formatter,
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "level": log_level,
            },
            "null": {
                "class": "logging.NullHandler",
            },
        },
        "loggers": {
            "dagster": {
                "handlers": [handler],
                "level": log_level,
            },
            # Only one of dagster or dagster-webserver will be used at a time. We configure them
            # both here to avoid a dependency on the dagster-webserver package.
            "dagit": {
                "handlers": [handler],
                "level": log_level,
            },
            "dagster-webserver": {
                "handlers": [handler],
                "level": log_level,
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

    # override the default warnings handler as per https://docs.python.org/3/library/warnings.html#warnings.showwarning
    # to use the same formatting
    def custom_warning_handler(message, category, filename, lineno, file=None, line=None):
        log_message = warnings.formatwarning(message, category, filename, lineno, line)
        logging.getLogger("dagster").warning(log_message)

    warnings.showwarning = custom_warning_handler


def create_console_logger(name: str, level: Union[str, int]) -> logging.Logger:
    klass = logging.getLoggerClass()
    logger = klass(name, level=level)
    coloredlogs.install(
        logger=logger,
        level=level,
        fmt=default_format_string(),
        datefmt=default_date_format_string(),
        field_styles={"levelname": {"color": "blue"}, "asctime": {"color": "green"}},
        level_styles={"debug": {}, "error": {"color": "red"}},
    )
    return logger
