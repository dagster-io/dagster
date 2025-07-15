from loguru import logger
import logging
import sys
import os

class DagsterLogHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)

def loguru_enabled():
    """Check if loguru is enabled via environment variable"""
    return os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes")

def get_loguru_config():
    """Get loguru configuration from environment variables"""
    return {
        "enable_loguru": os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes"),
        "log_level": os.getenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG"),
        "format": os.getenv("DAGSTER_LOGURU_FORMAT", "{time} | {level} | {message}"),
        "to_file": os.getenv("DAGSTER_LOGURU_TO_FILE", "true").lower() in ("true", "1", "yes"),
        "file_path": os.getenv("DAGSTER_LOGURU_FILE_PATH", "/tmp/dagster_loguru_output.log")
    }

# Configure loguru
logger.remove()
logger.add(sys.stderr, level="DEBUG")
logger.add(DagsterLogHandler(), level="DEBUG")
logger.success("This is a SUCCESS from loguru_bridge.py")

# Get configuration and conditionally add file logging
config = get_loguru_config()
if config.get("to_file", False):
    logger.add(
        config.get("file_path", "/tmp/dagster_loguru_output.log"),
        level=config.get("log_level", "DEBUG"),
        format=config.get("format", "{message}")
    )

# loguru_bridge.py
def dagster_context_sink(context):
    def sink_func(msg):
        record = msg.record
        level = record["level"].name.lower()
        log_method = getattr(context.log, level, context.log.info)
        log_method(record["message"])
    return sink_func

