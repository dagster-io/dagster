from dagster import check

from dagster.core.types.field_utils import check_user_facing_opt_field_param
from .config import resolve_config_field


class LoggerDefinition(object):
    '''Loggers are pipeline-scoped logging handlers, which will be automatically invoked whenever
    solids in a pipeline log messages.

    Args:
        logger_fn (Callable[[InitLoggerContext], logging.Logger]):
            User provided function to instantiate the logger. This logger will be automatically
            invoked whenever the methods on ``context.log`` are called.
        config_field (Field):
            The type for the configuration data for this logger, if any. Will be passed to
            ``logger_fn`` as ``init_context.logger_config``
        description (str):
            The string description of this logger.
    '''

    def __init__(self, logger_fn, config_field=None, description=None):
        self._logger_fn = check.callable_param(logger_fn, 'logger_fn')
        self._config_field = check_user_facing_opt_field_param(
            config_field, 'config_field', 'of a LoggerDefinition or @logger'
        )
        self._description = check.opt_str_param(description, 'description')

    @property
    def logger_fn(self):
        return self._logger_fn

    @property
    def config_field(self):
        return self._config_field

    @property
    def description(self):
        return self._description


def logger(config=None, config_field=None, description=None):
    '''A decorator for creating a logger. The decorated function will be used as the
    logger_fn in a LoggerDefinition.

    Args:
        config (Dict[str, Field]):
                The schema for the configuration data made available to the logger_fn
        config_field (Field):
            Used in the rare case of a top level config type other than a dictionary.

            Only one of config or config_field can be provided.
        description (str)
    '''
    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config):
        return LoggerDefinition(logger_fn=config)

    config_field = resolve_config_field(config_field, config, '@logger')

    def _wrap(logger_fn):
        return LoggerDefinition(logger_fn, config_field, description)

    return _wrap
