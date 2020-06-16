from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.definitions.config import is_callable_valid_config_arg
from dagster.utils.backcompat import canonicalize_backcompat_args, rename_warning


class LoggerDefinition(object):
    '''Core class for defining loggers.

    Loggers are pipeline-scoped logging handlers, which will be automatically invoked whenever
    solids in a pipeline log messages.

    Args:
        logger_fn (Callable[[InitLoggerContext], logging.Logger]): User-provided function to
            instantiate the logger. This logger will be automatically invoked whenever the methods
            on ``context.log`` are called from within solid compute logic.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.logger_config`.
        description (Optional[str]): A human-readable description of this logger.
    '''

    def __init__(self, logger_fn, config_schema=None, description=None, config=None):
        self._logger_fn = check.callable_param(logger_fn, 'logger_fn')
        self._config_schema = canonicalize_backcompat_args(
            check_user_facing_opt_config_param(config_schema, 'config_schema'),
            'config_schema',
            check_user_facing_opt_config_param(config, 'config'),
            'config',
            '0.9.0',
        )
        self._description = check.opt_str_param(description, 'description')

    @property
    def logger_fn(self):
        return self._logger_fn

    @property
    def config_field(self):
        rename_warning('config_schema', 'config_field', '0.9.0')
        return self._config_schema

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def description(self):
        return self._description


def logger(config_schema=None, description=None, config=None):
    '''Define a logger.

    The decorated function should accept an :py:class:`InitLoggerContext` and return an instance of
    :py:class:`python:logging.Logger`. This function will become the ``logger_fn`` of an underlying
    :py:class:`LoggerDefinition`.

    Args:
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.logger_config`.
        description (Optional[str]): A human-readable description of the logger.
    '''
    # This case is for when decorator is used bare, without arguments.
    # E.g. @logger versus @logger()
    if callable(config_schema) and not is_callable_valid_config_arg(config_schema):
        return LoggerDefinition(logger_fn=config_schema)

    def _wrap(logger_fn):
        return LoggerDefinition(
            logger_fn=logger_fn,
            config_schema=canonicalize_backcompat_args(
                config_schema, 'config_schema', config, 'config', '0.9.0'
            ),
            description=description,
        )

    return _wrap
