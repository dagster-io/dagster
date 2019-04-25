from dagster import check

from dagster.core.types import Field, Dict
from dagster.core.types.field_utils import check_user_facing_opt_field_param


class LoggerDefinition(object):
    '''Loggers are pipeline-scoped logging handlers, which will be automatically invoked whenever
    solids in a pipeline log messages.

    Args:
        logger_fn (Callable[[InitResourceContext], logging.Logger]):
            User provided function to instantiate the logger. This logger will be automatically
            invoked whenever the methods on ``context.log`` are called.
        config_field (Field):
            The type for the configuration data for this logger, if any. Will be passed to
            ``logger_fn`` as ``init_context.logger_config``
        description (str):
            The string description of this logger.
    '''

    def __init__(self, logger_fn, config_field=None, description=None):
        self.logger_fn = check.callable_param(logger_fn, 'logger_fn')
        self.config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a LoggerDefinition or @logger'
        )
        self.description = check.opt_str_param(description, 'description')


def logger(config_field=None, description=None):
    '''A decorator for creating a logger. The decorated function will be used as the
    logger_fn in a LoggerDefinition.
    '''

    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config_field):
        return LoggerDefinition(logger_fn=config_field, config_field=Field(Dict({})))

    def _wrap(logger_fn):
        return LoggerDefinition(logger_fn, config_field, description)

    return _wrap
