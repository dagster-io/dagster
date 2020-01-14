from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.definitions.config import is_callable_valid_config_arg


class LoggerDefinition(object):
    '''Core class for defining loggers.
    
    Loggers are pipeline-scoped logging handlers, which will be automatically invoked whenever
    solids in a pipeline log messages.

    Args:
        logger_fn (Callable[[InitLoggerContext], logging.Logger]): User-provided function to
            instantiate the logger. This logger will be automatically invoked whenever the methods
            on ``context.log`` are called from within solid compute logic.
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.logger_config`.
            This value can be a:
                - :py:class:`Field`
                - Python primitive types that resolve to dagster config types
                    - int, float, bool, str, list.
                - A dagster config type: Int, Float, Bool, List, Optional, :py:class:`Selector`, :py:class:`Dict`
                - A bare python dictionary, which is wrapped in Field(Dict(...)). Any values of
                in the dictionary get resolved by the same rules, recursively.
        description (Optional[str]): A human-readable description of this logger.
    '''

    def __init__(self, logger_fn, config=None, description=None):
        self._logger_fn = check.callable_param(logger_fn, 'logger_fn')
        self._config_field = check_user_facing_opt_config_param(config, 'config')
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


def logger(config=None, description=None):
    '''Define a logger.
    
    The decorated function should accept an :py:class:`InitLoggerContext` and return an instance of
    :py:class:`python:logging.Logger`. This function will become the ``logger_fn`` of an underlying
    :py:class:`LoggerDefinition`.

    Args:
        config (Optional[Any]): The schema for the config. Configuration data available in
            `init_context.logger_config`.
            This value can be a:
                - :py:class:`Field`
                - Python primitive types that resolve to dagster config types
                    - int, float, bool, str, list.
                - A dagster config type: Int, Float, Bool, List, Optional, :py:class:`Selector`, :py:class:`Dict`
                - A bare python dictionary, which is wrapped in Field(Dict(...)). Any values of
                in the dictionary get resolved by the same rules, recursively.
        config_field (Optional[Field]): Used in the rare case of a top level config type other than
            a dictionary.

            Only one of config or config_field can be provided.
        description (Optional[str]): A human-readable description of the logger.
    '''
    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config) and not is_callable_valid_config_arg(config):
        return LoggerDefinition(logger_fn=config)

    def _wrap(logger_fn):
        return LoggerDefinition(logger_fn, config, description)

    return _wrap
