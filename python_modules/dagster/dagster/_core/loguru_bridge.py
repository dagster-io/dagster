import logging
import os
import sys
import threading
from functools import wraps
from typing import Any

from loguru import logger


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


logging.basicConfig(handlers=[InterceptHandler()], level=0)


class LoguruConfigurator:
    """Configures the final output sink for Loguru.
    This version provides a rich default configuration that can be optionally
    overridden by environment variables for advanced users.
    """

    config: dict[str, Any]

    def __init__(self, enable_terminal_sink: bool = True):
        """Initializes the Loguru configuration. A singleton pattern is used
        to ensure this setup runs only once.
        """
        # This singleton pattern prevents re-running the configuration in the same process.
        if getattr(LoguruConfigurator, "_initialized", False):
            return

        self.config = self._load_config()
        if enable_terminal_sink:
            self._setup_sinks()

        # Mark as initialized to prevent re-setup.
        LoguruConfigurator._initialized = True

    def _load_config(self) -> dict[str, Any]:
        """Loads configuration, using sensible defaults that can be
        overridden by environment variables.
        """
        # Define a rich, informative default format for logs.
        default_format = (
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
        )

        return {
            # Defaults to 'true', but can be disabled by setting DAGSTER_LOGURU_ENABLED=false.
            "enabled": os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes"),
            # Defaults to 'DEBUG' level, but can be overridden by DAGSTER_LOGURU_LOG_LEVEL.
            "log_level": os.getenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG"),
            # Defaults to the rich format above, but can be overridden by DAGSTER_LOGURU_FORMAT.
            "format": os.getenv("DAGSTER_LOGURU_FORMAT", default_format),
        }

    def _setup_sinks(self) -> None:
        """Sets up the final Loguru sink for console output (stderr).
        This is the sink that will display logs in the terminal and Dagster UI.
        """
        if not self.config.get("enabled", False):
            return

        logger.remove()  # Remove any pre-existing sinks to ensure a clean setup.
        logger.add(
            sys.stderr,
            level=self.config["log_level"],
            format=self.config["format"],
            colorize=True,  # Always enable colorization; Loguru handles non-TTY cases.
        )


# This ensures that the logging system is ready as soon as the bridge is used.
loguru_config = LoguruConfigurator()


def dagster_context_sink(context):
    """Create a Loguru sink that forwards messages to a Dagster context."""
    log_state = threading.local()
    log_state.in_dagster_sink = False

    def sink(message):
        if getattr(log_state, "in_dagster_sink", False):
            return

        log_state.in_dagster_sink = True
        try:
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


def with_loguru_logger(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        _ = LoguruConfigurator(enable_terminal_sink=False)

        context = kwargs.get("context", None)
        if context is None and args and hasattr(args[0], "log"):
            context = args[0]

        if not (context and hasattr(context, "log")):
            return fn(*args, **kwargs)

        original_log_methods = {
            name: getattr(context.log, name)
            for name in ["debug", "info", "warning", "error", "critical"]
        }

        def make_proxy(level):
            def proxy_fn(msg):
                logger.opt(depth=1).log(level, msg)

            return proxy_fn

        for name, lvl in {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARNING",
            "error": "ERROR",
            "critical": "CRITICAL",
        }.items():
            setattr(context.log, name, make_proxy(lvl))

        try:
            return fn(*args, **kwargs)
        finally:
            for name, orig in original_log_methods.items():
                setattr(context.log, name, orig)

    return wrapper
