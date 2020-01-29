import logging
import socket

from dagster import Field, logger


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


@logger(
    {
        'log_level': Field(str, is_required=False, default_value='INFO'),
        'name': Field(str, is_required=False, default_value='dagster_papertrail'),
        'papertrail_address': Field(str, description='Papertrail URL', is_required=True),
        'papertrail_port': Field(int, description='Papertrail port', is_required=True),
    },
    description='A JSON-formatted console logger',
)
def papertrail_logger(init_context):
    level, name, papertrail_address, papertrail_port = (
        init_context.logger_config.get(k)
        for k in ('log_level', 'name', 'papertrail_address', 'papertrail_port')
    )

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    log_format = '%(asctime)s %(hostname)s ' + name + ': %(message)s'

    formatter = logging.Formatter(log_format, datefmt='%b %d %H:%M:%S')
    handler = logging.handlers.SysLogHandler(address=(papertrail_address, papertrail_port))
    handler.addFilter(ContextFilter())
    handler.setFormatter(formatter)

    logger_.addHandler(handler)

    return logger_
