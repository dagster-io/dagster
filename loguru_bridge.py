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
    Uses HTML-style formatting for Dagster UI and visible colors.
    """
    def sink_func(msg):
        record = msg.record
        level_name = record["level"].name
        
        # Get base message
        message = record["message"]
        
        # Add HTML styling based on level
        if level_name == "DEBUG":
            message = f"<span style='color:#9370DB;font-weight:bold'>DEBUG:</span> {message}"
        elif level_name == "INFO":
            message = f"<span style='color:#3CB371;font-weight:bold'>INFO:</span> {message}"
        elif level_name == "SUCCESS":
            message = f"<span style='color:#00FF7F;font-weight:bold'>SUCCESS:</span> {message}"  
        elif level_name == "WARNING":
            message = f"<span style='color:#FFD700;font-weight:bold'>WARNING:</span> {message}"
        elif level_name == "ERROR":
            message = f"<span style='color:#FF6347;font-weight:bold'>ERROR:</span> {message}"
        elif level_name == "CRITICAL":
            message = f"<span style='color:#FF0000;font-weight:bold'>CRITICAL:</span> {message}"
            
        # Map Loguru levels to Dagster levels
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

        # Use basic format for Docker/Dagster Cloud which will be HTML-enhanced
        # by the dagster_context_sink
        docker_format = "{message}"
        
        # Use nice formatting for local development
        local_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        
        # Environment variables
        os.environ["PYTHONUNBUFFERED"] = "1"
        
        logger.remove()
        
        # When in Docker/Cloud use plain format (will be HTML styled in sink)
        # Otherwise use colorful format for local development
        is_docker = os.environ.get("DAGSTER_CURRENT_IMAGE") is not None
        format_str = docker_format if is_docker else local_format
        
        logger.add(
            sys.stderr,
            level=self.config["log_level"],
            format=format_str,
            colorize=not is_docker,  # Disable colorize for Docker
            diagnose=True,
            enqueue=True,
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
