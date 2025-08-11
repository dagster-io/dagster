import inspect
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable

from loguru import logger


class InterceptHandler(logging.Handler):
    """Forwards standard logging records to Loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# This line runs on module import, patching the root logger to use our handler.
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class LoguruConfigurator:
    """Configures the Loguru sink with rich defaults, overridable by environment variables."""

    _initialized = False

    def __init__(self, enable_terminal_sink: bool = True):
        if LoguruConfigurator._initialized:
            return
        self.config = self.load_config()
        if enable_terminal_sink:
            self.setup_sinks()
        LoguruConfigurator._initialized = True

    @classmethod
    def reset(cls) -> None:
        """Reset the initialization state, primarily for testing purposes."""
        cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the LoguruConfigurator has been initialized."""
        return cls._initialized

    def load_config(self) -> dict[str, Any]:
        """Loads configuration from environment variables, with sensible defaults."""
        default_format = (
            "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
            "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
        )
        return {
            "enabled": os.getenv("DAGSTER_LOGURU_ENABLED", "true").lower() in ("true", "1", "yes"),
            "log_level": os.getenv("DAGSTER_LOGURU_LOG_LEVEL", "DEBUG"),
            "format": os.getenv("DAGSTER_LOGURU_FORMAT", default_format),
        }

    def setup_sinks(self) -> None:
        """Sets up the final Loguru sink to stderr."""
        if self.config.get("enabled", False):
            logger.remove()  # only clear sinks if Loguru logging is enabled
            logger.add(
                sys.stderr,
                level=self.config["log_level"],
                format=self.config["format"],
                colorize=True,
            )

    # Keep backward compatibility for tests that might still use the private methods
    _load_config = load_config
    _setup_sinks = setup_sinks


# Initialize the default sink configuration when the module is first imported.
loguru_config = LoguruConfigurator()


def dagster_context_sink(context: Any) -> Callable[[Any], None]:
    """Creates a Loguru sink that forwards logs to a Dagster context-aware logger."""

    def sink(message: Any) -> None:
        record = message.record
        level = record["level"].name
        msg = record["message"]
        extras = record["extra"] or {}

        level_map = {
            "TRACE": "debug",
            "DEBUG": "debug",
            "INFO": "info",
            "SUCCESS": "info",
            "WARNING": "warning",
            "ERROR": "error",
            "CRITICAL": "critical",
        }

        log_method_name = level_map.get(level, "info")

        # Fallback if context or log method is missing
        if not context or not hasattr(context, "log"):
            return

        log_method = getattr(context.log, log_method_name, None)
        if not callable(log_method):
            return

        try:
            sig = inspect.signature(log_method)
            if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
                log_method(msg, **extras)
            else:
                log_method(msg)
        except Exception:
            # best-effort fallback
            log_method(msg)

    return sink


def with_loguru_logger(fn: Callable) -> Callable:
    """Decorator that patches 'context.log' methods to redirect to 'loguru.logger'.
    This ensures that calls like 'context.log.info()' within an asset are also
    formatted by Loguru, providing a completely unified logging experience.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        context = kwargs.get("context", None)
        if context is None and args and hasattr(args[0], "log"):
            context = args[0]

        if not (context and hasattr(context, "log")):
            return fn(*args, **kwargs)

        # Save original context.log methods to restore them later.
        original_log_methods = {
            name: getattr(context.log, name)
            for name in ["debug", "info", "warning", "error", "critical"]
        }

        # Create proxy functions that forward calls to loguru.logger AND call the original method.
        def make_proxy(level: str, original_method: Callable) -> Callable[[str], None]:
            def proxy_fn(msg: str, *p_args, **p_kwargs) -> None:
                # Forward to loguru.logger
                logger.opt(depth=1).log(level, msg)
                # Also call the original method to maintain original behavior
                original_method(msg, *p_args, **p_kwargs)

            return proxy_fn

        # Replace context.log methods with our proxies.
        for name, lvl in {
            "debug": "DEBUG",
            "info": "INFO",
            "warning": "WARNING",
            "error": "ERROR",
            "critical": "CRITICAL",
        }.items():
            original = original_log_methods[name]
            setattr(context.log, name, make_proxy(lvl, original))

        try:
            return fn(*args, **kwargs)
        finally:
            # Restore the original context.log methods after execution.
            for name, orig in original_log_methods.items():
                setattr(context.log, name, orig)

    return wrapper
