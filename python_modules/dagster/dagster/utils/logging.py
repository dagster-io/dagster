import copy
import json
import logging
from logging import (CRITICAL, DEBUG, ERROR, INFO, WARNING)
import traceback

import coloredlogs

from dagster import check

# This global, while fundamentally offensive, is necessary if I want to be able
# to apply a blanket logging level after the fact based on context
REGISTERED_LOGGERS = set()

class CompositeLogger:
    def __init__(self, loggers=None, level=logging.ERROR):
        self.loggers = check.opt_list_param(loggers, 'loggers', of_type=logging.Logger)

        for logger in self.loggers:
            logger.setLevel(level)

    def __getattr__(self, name):
        def _invoke_logger_method(*args, **kwargs):
            for logger in self.loggers:
                logger_method = check.is_callable(getattr(logger, name))
                logger_method(*args, **kwargs)
        return _invoke_logger_method

class JsonFileHandler(logging.Handler):
    def __init__(self, json_path):
        super().__init__()
        self.json_path = json_path

    def emit(self, record):
        try:
            logged_properties = copy.copy(record.__dict__)
            del logged_properties['msg']
            with open(self.json_path, 'a') as ff:
                text_line = json.dumps(logged_properties)
                ff.write(text_line + '\n')
        # Need to catch Exception here, so disabling lint
        except Exception as e: # pylint: disable=W0703
            logging.critical('Error during logging!')
            logging.exception(str(e))


def define_json_file_logger(name, json_path, level):
    check.str_param(name, 'name')

    if name in REGISTERED_LOGGERS:
        return logging.getLogger(name)

    logger = logging.getLogger(name)
    logger.setLevel(level)


    stream_handler = JsonFileHandler(json_path)
    stream_handler.setFormatter(define_default_formatter())
    logger.addHandler(stream_handler)

    return logger


def define_logger(name, level=INFO):
    check.str_param(name, 'name')

    if name in REGISTERED_LOGGERS:
        return logging.getLogger(name)

    logger = logging.getLogger(name)

    # This is the pre-coloredlogs process. Retaining here for posterity
    # stream_handler = logging.StreamHandler()
    # logger.setLevel(INFO)
    # stream_handler.setFormatter(define_default_formatter())
    # logger.addHandler(stream_handler)

    coloredlogs.install(logger=logger, level=level, fmt=default_format_string())

    REGISTERED_LOGGERS.add(name)

    return logger

def set_global_logging_level(level):
    check.param_invariant(
        level in {DEBUG, INFO, WARNING, ERROR, CRITICAL},
        'Invalid logging level {level}'.format(level=level)
    )
    for logger in REGISTERED_LOGGERS:
        logging.getLogger(logger).setLevel(level)

def add_global_handler(handler):
    handler.setFormatter(define_default_formatter())
    for logger in REGISTERED_LOGGERS:
        logging.getLogger(logger).addHandler(handler)

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
    return ''.join(traceback.format_tb(exception.__traceback__))
