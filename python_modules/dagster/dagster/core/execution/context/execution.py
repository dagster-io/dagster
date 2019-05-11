from collections import namedtuple
import logging
from dagster import check
from dagster.utils.logging import INFO, define_colored_console_logger


class ExecutionContext(namedtuple('_ExecutionContext', 'loggers resources tags')):
    '''
    The user-facing object in the context creation function. The user constructs
    this in order to effect the context creation process. This could be named
    SystemPipelineExecutionContextCreationData although that seemed excessively verbose.

    Args:
        loggers (List[Logger]):
        resources ():
        tags (dict[str, str])
    '''

    def __new__(cls, loggers=None, resources=None, tags=None):
        return super(ExecutionContext, cls).__new__(
            cls,
            loggers=check.opt_list_param(loggers, 'loggers', logging.Logger),
            resources=resources,
            tags=check.opt_dict_param(tags, 'tags'),
        )

    @staticmethod
    def console_logging(log_level=INFO, resources=None):
        return ExecutionContext(
            loggers=[define_colored_console_logger('dagster', log_level)], resources=resources
        )
