import os
import sys
import logging
from functools import wraps
from loguru import logger

def loguru_enabled():
    """Check if loguru is enabled based on environment variables."""
    value = os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower()
    if value in ("false", "0", "no"):
        return False
    return True  # Default to True for any other value, including invalid ones

class DagsterLogHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)

def dagster_context_sink(context):
    """
    A Loguru sink that correctly forwards records to the Dagster context logger.
    It preserves ANSI color codes for Docker and CI environments.
    """
    def sink_func(msg):
        record = msg.record
        level_name = record["level"].name
        
        # Get colored message directly from loguru
        colored_message = msg.message
        
        # For colored console in Docker
        if os.environ.get("DAGSTER_DOCKER_COLORED_LOGS_ENABLED", "true").lower() in ("true", "1", "yes"):
            message = colored_message
        else:
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

        # Force colors for Docker and CI environments
        os.environ["FORCE_COLOR"] = "1"
        os.environ["TERM"] = os.environ.get("TERM", "xterm-256color")
        os.environ["DAGSTER_DOCKER_COLORED_LOGS_ENABLED"] = "true"
        os.environ["PYTHONUNBUFFERED"] = "1"  # Unbuffered output for Docker
        
        # Enhanced format with bright colors for better visibility in Docker/CI
        docker_format = os.getenv(
            "DAGSTER_DOCKER_LOGURU_FORMAT",
            "<bright_green>{time:HH:mm:ss}</bright_green> | <level>{level: <8}</level> | <bright_cyan>{name}</bright_cyan>:<bright_cyan>{function}</bright_cyan> - <level>{message}</level>"
        )
        
        logger.remove()
        
        # Add normal stderr sink
        logger.add(
            sys.stderr,
            level=self.config["log_level"],
            format=self.config["format"] if not os.environ.get("DAGSTER_CURRENT_IMAGE") else docker_format,
            colorize=True,
            diagnose=True,
            enqueue=True,
            backtrace=True,
        )

loguru_config = LoguruConfigurator()

def with_loguru_logger(fn):
    """
    Decorator to add a Dagster context-aware sink for the duration of an asset's execution.
    This is the recommended way to integrate Loguru with Dagster.
    """
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        # Get the actual context from self._context or use self if it has log attribute
        context = getattr(self, '_context', self) if not hasattr(self, 'log') else self
        
        handler_id = logger.add(dagster_context_sink(context), level="DEBUG")
        try:
            # Don't add context to the arguments, it should be already available via self._context
            result = fn(self, *args, **kwargs)
        finally:
            logger.remove(handler_id)
        return result

    return wrapper
