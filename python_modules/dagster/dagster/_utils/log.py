import copy
import logging
import sys
import traceback
from contextlib import contextmanager
from typing import Dict, NamedTuple, Optional

import coloredlogs
import pendulum

import dagster._check as check
import dagster._seven as seven
from dagster._config import Enum, EnumValue
from dagster._core.definitions.logger_definition import logger
from dagster._core.utils import PYTHON_LOGGING_LEVELS_MAPPING, coerce_valid_log_level

LogLevelEnum = Enum("log_level", list(map(EnumValue, PYTHON_LOGGING_LEVELS_MAPPING.keys())))


class JsonFileHandler(logging.Handler):
    def __init__(self, json_path: str):
        super(JsonFileHandler, self).__init__()
        self.json_path = check.str_param(json_path, "json_path")

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_dict = copy.copy(record.__dict__)

            # This horrific monstrosity is to maintain backwards compatability
            # with the old behavior of the JsonFileHandler, which the clarify
            # project has a dependency on. It relied on the dagster-defined
            # properties smashing all the properties of the LogRecord object
            # and uploads all of those properties to a redshift table for
            # in order to do analytics on the log

            if "dagster_meta" in log_dict:
                dagster_meta_dict = log_dict["dagster_meta"]
                del log_dict["dagster_meta"]
            else:
                dagster_meta_dict = {}

            log_dict.update(dagster_meta_dict)

            with open(self.json_path, "a", encoding="utf8") as ff:
                text_line = seven.json.dumps(log_dict)
                ff.write(text_line + "\n")
        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[%s] Error during logging!", self.__class__.__name__)
            logging.exception(str(e))


class StructuredLoggerMessage(
    NamedTuple(
        "_StructuredLoggerMessage",
        [
            ("name", str),
            ("message", str),
            ("level", int),
            ("meta", Dict[object, object]),
            ("record", logging.LogRecord),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        message: str,
        level: int,
        meta: Dict[object, object],
        record: logging.LogRecord,
    ):
        return super(StructuredLoggerMessage, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(message, "message"),
            coerce_valid_log_level(level),
            check.dict_param(meta, "meta"),
            check.inst_param(record, "record", logging.LogRecord),
        )


class JsonEventLoggerHandler(logging.Handler):
    def __init__(self, json_path: str, construct_event_record):
        super(JsonEventLoggerHandler, self).__init__()
        self.json_path = check.str_param(json_path, "json_path")
        self.construct_event_record = construct_event_record

    def emit(self, record: logging.LogRecord) -> None:
        try:
            event_record = self.construct_event_record(record)
            with open(self.json_path, "a", encoding="utf8") as ff:
                text_line = seven.json.dumps(event_record.to_dict())
                ff.write(text_line + "\n")

        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[%s] Error during logging!", self.__class__.__name__)
            logging.exception(str(e))


class StructuredLoggerHandler(logging.Handler):
    def __init__(self, callback):
        super(StructuredLoggerHandler, self).__init__()
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
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[%s] Error during logging!", self.__class__.__name__)
            logging.exception(str(e))


def construct_single_handler_logger(name, level, handler):
    check.str_param(name, "name")
    check.inst_param(handler, "handler", logging.Handler)

    level = coerce_valid_log_level(level)

    @logger
    def single_handler_logger(_init_context):
        klass = logging.getLoggerClass()
        logger_ = klass(name, level=level)
        logger_.addHandler(handler)
        handler.setLevel(level)
        return logger_

    return single_handler_logger


# Base python logger whose messages will be captured as structured Dagster log messages.
BASE_DAGSTER_LOGGER = logging.getLogger(name="dagster")


def get_dagster_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Creates a python logger whose output messages will be captured and converted into Dagster log
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


def define_structured_logger(name, callback, level):
    check.str_param(name, "name")
    check.callable_param(callback, "callback")
    level = coerce_valid_log_level(level)

    return construct_single_handler_logger(name, level, StructuredLoggerHandler(callback))


def define_json_file_logger(name, json_path, level):
    check.str_param(name, "name")
    check.str_param(json_path, "json_path")
    level = coerce_valid_log_level(level)

    stream_handler = JsonFileHandler(json_path)
    stream_handler.setFormatter(define_default_formatter())
    return construct_single_handler_logger(name, level, stream_handler)


def get_stack_trace_array(exception):
    check.inst_param(exception, "exception", Exception)
    if hasattr(exception, "__traceback__"):
        tb = exception.__traceback__
    else:
        _exc_type, _exc_value, tb = sys.exc_info()
    return traceback.format_tb(tb)


def _mockable_formatTime(record, datefmt=None):  # pylint: disable=unused-argument
    """Uses pendulum.now to determine the logging time, causing pendulum
    mocking to affect the logger timestamp in tests."""
    return pendulum.now().strftime(datefmt if datefmt else default_date_format_string())


def default_format_string():
    return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def default_date_format_string():
    return "%Y-%m-%d %H:%M:%S %z"


def define_default_formatter():
    return logging.Formatter(default_format_string(), default_date_format_string())


@contextmanager
def quieten(quiet=True, level=logging.WARNING):
    if quiet:
        logging.disable(level)
    try:
        yield
    finally:
        if quiet:
            logging.disable(logging.NOTSET)


def configure_loggers(handler="default", log_level="INFO"):
    LOGGING_CONFIG = {
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
        },
        "handlers": {
            "default": {
                "formatter": "colored",
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
                "level": "INFO",
            },
            "dagit": {
                "handlers": [handler],
                "level": "INFO",
            },
        },
    }

    logging.config.dictConfig(LOGGING_CONFIG)

    if handler == "default":
        for name in ["dagster", "dagit"]:
            logging.getLogger(name).handlers[0].formatter.formatTime = _mockable_formatTime
