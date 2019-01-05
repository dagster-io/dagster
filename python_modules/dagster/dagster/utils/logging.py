from __future__ import absolute_import
from collections import namedtuple
import copy
import json
import logging
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING
import traceback

import coloredlogs

from dagster import check

VALID_LEVELS = set([CRITICAL, DEBUG, ERROR, INFO, WARNING])

LOOKUP = {'CRITICAL': CRITICAL, 'DEBUG': DEBUG, 'ERROR': ERROR, 'INFO': INFO, 'WARNING': WARNING}


def level_from_string(string):
    check.str_param(string, 'string')
    return LOOKUP[string]


class CompositeLogger(object):
    def __init__(self, loggers=None):
        self.loggers = check.opt_list_param(loggers, 'loggers', of_type=logging.Logger)

    def __getattr__(self, name):
        def _invoke_logger_method(*args, **kwargs):
            for logger in self.loggers:
                logger_method = check.is_callable(getattr(logger, name))
                logger_method(*args, **kwargs)

        return _invoke_logger_method


class JsonFileHandler(logging.Handler):
    def __init__(self, json_path):
        super(JsonFileHandler, self).__init__()
        self.json_path = check.str_param(json_path, 'json_path')

    def emit(self, record):
        try:
            log_dict = copy.copy(record.__dict__)

            # This horrific monstrosity is to maintain backwards compatability
            # with the old behavior of the JsonFileHandler, which the clarify
            # project has a dependency on. It relied on the dagster-defined
            # properties smashing all the properties of the LogRecord object
            # and uploads all of those properties to a redshift table for
            # in order to do analytics on the log

            if 'dagster_meta' in log_dict:
                dagster_meta_dict = log_dict['dagster_meta']
                del log_dict['dagster_meta']
            else:
                dagster_meta_dict = {}

            log_dict.update(dagster_meta_dict)

            with open(self.json_path, 'a') as ff:
                text_line = json.dumps(log_dict)
                ff.write(text_line + '\n')
        # Need to catch Exception here, so disabling lint
        except Exception as e:  # pylint: disable=W0703
            logging.critical('Error during logging!')
            logging.exception(str(e))


class StructuredLoggerMessage(
    namedtuple('_StructuredLoggerMessage', 'name message level meta record')
):
    def __new__(cls, name, message, level, meta, record):
        return super(StructuredLoggerMessage, cls).__new__(
            cls,
            check.str_param(name, 'name'),
            check.str_param(message, 'message'),
            check_valid_level_param(level),
            check.dict_param(meta, 'meta'),
            check.inst_param(record, 'record', logging.LogRecord),
        )


class StructuredLoggerHandler(logging.Handler):
    def __init__(self, callback):
        super(StructuredLoggerHandler, self).__init__()
        self.callback = check.is_callable(callback, 'callback')

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
            logging.critical('Error during logging!')
            logging.exception(str(e))


def check_valid_level_param(level):
    check.param_invariant(
        level in VALID_LEVELS,
        'level',
        'Must be valid python logging level. Got {level}'.format(level=level),
    )
    return level


def construct_single_handler_logger(name, level, handler):
    check.str_param(name, 'name')
    check_valid_level_param(level)
    check.inst_param(handler, 'handler', logging.Handler)

    klass = logging.getLoggerClass()
    logger = klass(name, level=level)
    logger.addHandler(handler)
    return logger


def define_structured_logger(name, callback, level):
    check.str_param(name, 'name')
    check.callable_param(callback, 'callback')
    check_valid_level_param(level)

    return construct_single_handler_logger(name, level, StructuredLoggerHandler(callback))


def define_json_file_logger(name, json_path, level):
    check.str_param(name, 'name')
    check.str_param(json_path, 'json_path')
    check_valid_level_param(level)

    stream_handler = JsonFileHandler(json_path)
    stream_handler.setFormatter(define_default_formatter())
    return construct_single_handler_logger(name, level, stream_handler)


def define_colored_console_logger(name, level=INFO):
    check.str_param(name, 'name')
    check.param_invariant(
        level in VALID_LEVELS,
        'level',
        'Must be valid python logging level. Got {level}'.format(level=level),
    )

    klass = logging.getLoggerClass()
    logger = klass(name, level=level)
    coloredlogs.install(logger=logger, level=level, fmt=default_format_string())
    return logger


def default_format_string():
    return '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


def define_default_formatter():
    return logging.Formatter(default_format_string())


def debug_format_string():
    return '''%(name)s.%(levelname)s: %(message)s
    time: %(asctime)s relative: %(relativeCreated)dms
    path: %(pathname)s line: %(lineno)d'''


def define_debug_formatter():
    return logging.Formatter(debug_format_string())


def get_formatted_stack_trace(exception):
    check.inst_param(exception, 'exception', Exception)
    if hasattr(exception, '__traceback__'):
        tb = exception.__traceback__
    else:
        import sys

        _exc_type, _exc_value, tb = sys.exc_info()
    return ''.join(traceback.format_tb(tb))
