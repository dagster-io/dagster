import os
import sys
import logging
from functools import wraps
from loguru import logger

class DagsterLogHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)

def dagster_context_sink(context):
    """
    A Loguru sink that correctly forwards records to the Dagster context logger.
    It passes plain messages and relies on the Dagster UI for styling.
    """
    def sink_func(msg):
        record = msg.record
        level_name = record["level"].name
        message = record["message"]

        level_map = {
            "TRACE": "debug",
            "DEBUG": "debug",
            "INFO": "info",
            "SUCCESS": "info",     
            "WARNING": "warning",
            "ERROR": "error",
            "CRITICAL": "critical",
        }
        
        dagster_log_method_name = level_map.get(level_name, "info")
        log_method = getattr(context.log, dagster_log_method_name)
        log_method(message)

    return sink_func

class LoguruConfigurator:
    def __init__(self):
        self._sinks = {}
        self.config = self._load_config()

        if getattr(LoguruConfigurator, "_initialized", False):
            return

        self._setup_sinks()
        LoguruConfigurator._initialized = True

    def _load_config(self):
        return {
            "enabled": os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes"),
            "log_level": os.getenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG"),
            "format": os.getenv(
                "DAGSTER_LOGURU_FORMAT",
                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
            ),
        }

    def _setup_sinks(self):
        if not self.config["enabled"]:
            return

        logger.remove()
        logger.add(
            sys.stderr,
            level=self.config["log_level"],
            format=self.config["format"],
            colorize=True,
        )

loguru_config = LoguruConfigurator()

def with_loguru_logger(fn):
    """
    Decorator to add a Dagster context-aware sink for the duration of an asset's execution.
    This is the recommended way to integrate Loguru with Dagster.
    """
    @wraps(fn)
    def wrapper(context, *args, **kwargs):
        handler_id = logger.add(dagster_context_sink(context), level="DEBUG")
        try:
            result = fn(context, *args, **kwargs)
        finally:
            logger.remove(handler_id)
        return result

    return wrapper
