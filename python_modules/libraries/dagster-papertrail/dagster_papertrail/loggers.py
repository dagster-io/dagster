import logging
import socket

from dagster import Field, IntSource, StringSource, logger


class ContextFilter(logging.Filter):
    hostname = socket.gethostname()

    def filter(self, record):
        record.hostname = ContextFilter.hostname
        return True


@logger(
    {
        "log_level": Field(StringSource, is_required=False, default_value="INFO"),
        "name": Field(StringSource, is_required=False, default_value="dagster_papertrail"),
        "papertrail_address": Field(StringSource, description="Papertrail URL", is_required=True),
        "papertrail_port": Field(IntSource, description="Papertrail port", is_required=True),
    },
    description="A JSON-formatted console logger",
)
def papertrail_logger(init_context):
    """Use this logger to configure your Dagster pipeline to log to Papertrail. You'll need an
    active Papertrail account with URL and port.

    Example:

    .. code-block:: python

        @solid(required_resource_keys={'pagerduty'})
        def pagerduty_solid(context):
            context.resources.pagerduty.EventV2_create(
                summary='alert from dagster'
                source='localhost',
                severity='error',
                event_action='trigger',
            )

        @pipeline(
            mode_defs=[ModeDefinition(resource_defs={'pagerduty': pagerduty_resource})],
        )
        def pd_pipeline():
            pagerduty_solid()

        execute_pipeline(
            pd_pipeline,
            {
                'resources': {
                    'pagerduty': {'config': {'routing_key': '0123456789abcdef0123456789abcdef'}}
                }
            },
        )
    """
    level, name, papertrail_address, papertrail_port = (
        init_context.logger_config.get(k)
        for k in ("log_level", "name", "papertrail_address", "papertrail_port")
    )

    klass = logging.getLoggerClass()
    logger_ = klass(name, level=level)

    log_format = "%(asctime)s %(hostname)s " + name + ": %(message)s"

    formatter = logging.Formatter(log_format, datefmt="%b %d %H:%M:%S")
    handler = logging.handlers.SysLogHandler(address=(papertrail_address, papertrail_port))
    handler.addFilter(ContextFilter())
    handler.setFormatter(formatter)

    logger_.addHandler(handler)

    return logger_
