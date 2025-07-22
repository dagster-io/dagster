import os
import sys
import logging
from functools import wraps
from loguru import logger
import threading
# Redirect all standard Python logging (used by Dagster internals) to Loguru
class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            # Get Loguru level
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        # Find the real caller so logs point to the right source
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())
# Replace Python's root logger handlers with Loguru interception
logging.basicConfig(handlers=[InterceptHandler()], level=0)
# Configure Loguru: pick up env vars for level/format/color
class LoguruConfigurator:
    def __init__(self, enable_terminal_sink=True):
        if getattr(LoguruConfigurator, "_initialized", False):
            return
        self.config = self._load_config()
        if enable_terminal_sink:
            self._setup_sinks()
        LoguruConfigurator._initialized = True
    def _load_config(self):
        return {
            "enabled": os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes"),
            "log_level": os.getenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG"),
            "format": os.getenv("DAGSTER_LOGURU_FORMAT",
                                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                                "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"),
        }
    def _setup_sinks(self):
        if not self.config["enabled"]:
            return
        # Remove existing sinks, add our colored stderr sink
        logger.remove()
        logger.add(sys.stderr, level=self.config["log_level"], format=self.config["format"], colorize=True)
loguru_config = None
log_state = threading.local()
log_state.in_dagster_sink = False
def dagster_context_sink(context):
    """Create a Loguru sink that forwards messages to a Dagster context."""
    def sink(message):
        # Prevent infinite recursion when Dagster logs are intercepted by Loguru
        if getattr(log_state, "in_dagster_sink", False):
            return
            
        log_state.in_dagster_sink = True
        try:
            # Map Loguru levels to Dagster log methods
            level = message.record["level"].name
            msg = message.record["message"]
            
            if level == "TRACE" or level == "DEBUG":
                context.log.debug(msg)
            elif level == "INFO" or level == "SUCCESS":
                context.log.info(msg)
            elif level == "WARNING":
                context.log.warning(msg)
            elif level == "ERROR":
                context.log.error(msg)
            elif level == "CRITICAL":
                context.log.critical(msg)
        finally:
            log_state.in_dagster_sink = False
    
    return sink
# Decorator: Replace context.log methods with Loguru, so context.log.info(...) uses Loguru
def with_loguru_logger(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        global loguru_config
        if not loguru_config:
            loguru_config = LoguruConfigurator(enable_terminal_sink=False)
        context = kwargs.get("context", None)
        if context is None and args and hasattr(args[0], "log"):
            context = args[0]
        if not (context and hasattr(context, "log")):
            return fn(*args, **kwargs)
        # Save original context.log methods
        original_log_methods = {}
        for name in ["debug", "info", "warning", "error", "critical"]:
            original_log_methods[name] = getattr(context.log, name)
        # Replace context.log methods with Loguru proxies
        def make_proxy(level):
            def proxy_fn(msg):
                logger.opt(depth=1).log(level, msg)
            return proxy_fn
        for name, lvl in {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARNING",
            "error": "ERROR",
            "critical": "CRITICAL"
        }.items():
            setattr(context.log, name, make_proxy(lvl))
        try:
            return fn(*args, **kwargs)
        finally:
            # Restore original context.log methods after execution
            for name, orig in original_log_methods.items():
                setattr(context.log, name, orig)
    return wrapper
