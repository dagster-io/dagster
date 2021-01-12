import copy
import logging
import sys
import traceback
from collections import namedtuple
from contextlib import contextmanager

from dagster import check, seven
from dagster.config import Enum, EnumValue
from dagster.core.definitions.logger import logger
from dagster.core.log_manager import PYTHON_LOGGING_LEVELS_MAPPING, coerce_valid_log_level

LogLevelEnum = Enum("log_level", list(map(EnumValue, PYTHON_LOGGING_LEVELS_MAPPING.keys())))


class JsonFileHandler(logging.Handler):
    def __init__(self, json_path):
        super(JsonFileHandler, self).__init__()
        self.json_path = check.str_param(json_path, "json_path")

    def emit(self, record):
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

            with open(self.json_path, "a") as ff:
                text_line = seven.json.dumps(log_dict)
                ff.write(text_line + "\n")
        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[{}] Error during logging!".format(self.__class__.__name__))
            logging.exception(str(e))


class StructuredLoggerMessage(
    namedtuple("_StructuredLoggerMessage", "name message level meta record")
):
    def __new__(cls, name, message, level, meta, record):
        return super(StructuredLoggerMessage, cls).__new__(
            cls,
            check.str_param(name, "name"),
            check.str_param(message, "message"),
            coerce_valid_log_level(level),
            check.dict_param(meta, "meta"),
            check.inst_param(record, "record", logging.LogRecord),
        )


class JsonEventLoggerHandler(logging.Handler):
    def __init__(self, json_path, construct_event_record):
        super(JsonEventLoggerHandler, self).__init__()
        self.json_path = check.str_param(json_path, "json_path")
        self.construct_event_record = construct_event_record

    def emit(self, record):
        try:
            event_record = self.construct_event_record(record)
            with open(self.json_path, "a") as ff:
                text_line = seven.json.dumps(event_record.to_dict())
                ff.write(text_line + "\n")

        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[{}] Error during logging!".format(self.__class__.__name__))
            logging.exception(str(e))


class StructuredLoggerHandler(logging.Handler):
    def __init__(self, callback):
        super(StructuredLoggerHandler, self).__init__()
        self.callback = check.is_callable(callback, "callback")

    def emit(self, record):
        try:
            self.callback(
                StructuredLoggerMessage(
                    name=record.name,
                    message=record.msg,
                    level=record.levelno,
                    meta=record.dagster_meta,
                    record=record,
                )
            )
        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical("[{}] Error during logging!".format(self.__class__.__name__))
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


def default_format_string():
    return "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def define_default_formatter():
    return logging.Formatter(default_format_string())


@contextmanager
def quieten(quiet=True, level=logging.WARNING):
    if quiet:
        logging.disable(level)
    try:
        yield
    finally:
        if quiet:
            logging.disable(logging.NOTSET)
