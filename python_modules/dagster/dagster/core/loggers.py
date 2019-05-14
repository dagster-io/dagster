import logging

import coloredlogs

from dagster.core.types import Dict, Field, String
from dagster.core.definitions.logger import logger
from dagster.core.log_manager import coerce_valid_log_level
from dagster.utils.log import default_format_string


@logger(
    config_field=Field(
        Dict(
            {
                'log_level': Field(String, is_optional=True, default_value='INFO'),
                'name': Field(String, is_optional=True, default_value='dagster'),
            }
        )
    ),
    description='The default colored console logger.',
)
def colored_console_logger(init_context):
    level = coerce_valid_log_level(init_context.logger_config['log_level'])
    name = init_context.logger_config['name']

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)
    coloredlogs.install(logger=logger_, level=level, fmt=default_format_string())
    return logger_


def default_system_loggers():
    '''If users don't provide configuration for any loggers, we instantiate these loggers with the
    default config.

    Returns:
        List[Tuple[LoggerDefinition, dict]]: Default loggers and their associated configs.'''
    return [(colored_console_logger, {'name': 'dagster', 'log_level': 'INFO'})]


def default_loggers():
    return {'console': colored_console_logger}
