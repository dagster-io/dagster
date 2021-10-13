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

        @job(logger_defs={
            "console": colored_console_logger,
            "papertrail": papertrail_logger,
        })
        def simple_job():
            ...


        simple_job.execute_in_process(
            run_config={
                "loggers": {
                    "console": {
                        "config": {
                            "log_level": "INFO",
                        }
                    },
                    "papertrail": {
                        "config": {
                            "log_level": "INFO",
                            "name": "hello_pipeline",
                            "papertrail_address": "127.0.0.1",
                            "papertrail_port": 12345,
                        }
                    },
                }
            }
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
