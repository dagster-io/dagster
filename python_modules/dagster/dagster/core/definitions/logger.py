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

            This value can be any of:

            1. A Python primitive type that resolves to a Dagster config type 
               (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
               :py:class:`~python:str`, or :py:class:`~python:list`).

            2. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.Float`,
               :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
               :py:data:`~dagster.StringSource`, :py:data:`~dagster.Path`, :py:data:`~dagster.Any`,
               :py:class:`~dagster.Array`, :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`,
               :py:class:`~dagster.Selector`, :py:class:`~dagster.Shape`, or
               :py:class:`~dagster.Permissive`.

            3. A bare python dictionary, which will be automatically wrapped in
               :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
               according to the same rules.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. An instance of :py:class:`~dagster.Field`.

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

            This value can be any of:

            1. A Python primitive type that resolves to a Dagster config type 
               (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
               :py:class:`~python:str`, or :py:class:`~python:list`).

            2. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.Float`,
               :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
               :py:data:`~dagster.StringSource`, :py:data:`~dagster.Path`, :py:data:`~dagster.Any`,
               :py:class:`~dagster.Array`, :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`,
               :py:class:`~dagster.Selector`, :py:class:`~dagster.Shape`, or
               :py:class:`~dagster.Permissive`.

            3. A bare python dictionary, which will be automatically wrapped in
               :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
               according to the same rules.

            4. A bare python list of length one which itself is config type.
               Becomes :py:class:`Array` with list element as an argument.

            5. An instance of :py:class:`~dagster.Field`.

        description (Optional[str]): A human-readable description of the logger.
    '''
    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config) and not is_callable_valid_config_arg(config):
        return LoggerDefinition(logger_fn=config)

    def _wrap(logger_fn):
        return LoggerDefinition(logger_fn, config, description)

    return _wrap
