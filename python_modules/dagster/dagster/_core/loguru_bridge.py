import inspect
import logging
import os
import sys
from functools import wraps
from typing import Any, Callable

from loguru import logger


class InterceptHandler(logging.Handler):
    """Forwards standard Python logging records to the Loguru sink.
    Any log emitted by the 'logging' module will be intercepted and reformatted.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Retrieve the Loguru level name corresponding to the record's level number.
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find the frame that originated the log call to preserve correct stack information.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        # Forward the log to Loguru, preserving exception info and correct depth.
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


# This line runs once on module import, patching the root logger to use our handler.
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


class LoguruConfigurator:
    """Configures the Loguru sink with rich defaults that can be overridden by environment variables.
    Uses a singleton pattern to ensure it only runs once per process.
    """

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
        """Resets the initialization state, primarily for testing purposes."""
        cls._initialized = False

    @classmethod
    def is_initialized(cls) -> bool:
        """Checks if the configurator has been initialized."""
        return cls._initialized

    def load_config(self) -> dict[str, Any]:
        """Loads configuration from environment variables, providing sensible defaults."""
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
        """Sets up the final Loguru sink, typically to stderr for the terminal and Dagster UI."""
        if self.config.get("enabled", False):
            logger.remove()  # Clear any existing sinks to ensure a single, consistent output.
            logger.add(
                sys.stderr,
                level=self.config["log_level"],
                format=self.config["format"],
                colorize=True,  # Loguru automatically disables color for non-TTY outputs.
            )

    # Alias private methods for backward compatibility with older tests.
    _load_config = load_config
    _setup_sinks = setup_sinks


# Initialize the default sink configuration when this module is first imported.
loguru_config = LoguruConfigurator()


def dagster_context_sink(context: Any) -> Callable[[Any], None]:
    """Creates a Loguru sink that forwards logs to a Dagster context's logger.
    This is useful in tests or specific scenarios where logs need to be
    channeled through a mock or real 'context.log' object.
    """

    def sink(message: Any) -> None:
        record = message.record
        level = record["level"].name
        msg = record["message"]
        extras = record.get("extra", {})

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

        if not (context and hasattr(context, "log")):
            return

        log_method = getattr(context.log, log_method_name, None)
        if not callable(log_method):
            return
        # Introspect the log method to see if it accepts **kwargs.
        # This makes the sink robust against different logger implementations.
        try:
            sig = inspect.signature(log_method)
            if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
                log_method(msg, **extras)
            else:
                log_method(msg)
        except Exception:
            # Fallback to a simple call if inspection fails.
            log_method(msg)

    return sink


def with_loguru_logger(fn: Callable) -> Callable:
    """Decorator that patches 'context.log' methods to redirect to 'loguru.logger'.
    This provides a completely unified logging experience and is async-aware.
    """

    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        context = kwargs.get("context", None)
        if context is None and args and hasattr(args[0], "log"):
            context = args[0]
        if not (context and hasattr(context, "log")):
            return fn(*args, **kwargs)

        original_log_methods = {
            name: getattr(context.log, name)
            for name in ["debug", "info", "warning", "error", "critical"]
            if hasattr(context.log, name)  # This check makes it robust against simple mocks.
        }

        def make_proxy(level: str) -> Callable:
            def proxy_fn(msg: str, *p_args: Any, **p_kwargs: Any) -> None:
                logger.bind(**p_kwargs).opt(depth=1).log(level, msg.format(*p_args))

            return proxy_fn

        for name in original_log_methods:
            lvl = name.upper()
            setattr(context.log, name, make_proxy(lvl))

        try:
            return fn(*args, **kwargs)
        finally:
            for name, orig in original_log_methods.items():
                setattr(context.log, name, orig)

    if inspect.iscoroutinefunction(fn):

        @wraps(fn)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            context = kwargs.get("context", None)
            if context is None and args and hasattr(args[0], "log"):
                context = args[0]
            if not (context and hasattr(context, "log")):
                return await fn(*args, **kwargs)

            original_log_methods = {
                name: getattr(context.log, name)
                for name in ["debug", "info", "warning", "error", "critical"]
                if hasattr(context.log, name)
            }

            def make_proxy(level: str) -> Callable:
                def proxy_fn(msg: str, *p_args: Any, **p_kwargs: Any) -> None:
                    logger.bind(**p_kwargs).opt(depth=1).log(level, msg.format(*p_args))

                return proxy_fn

            for name in original_log_methods:
                lvl = name.upper()
                setattr(context.log, name, make_proxy(lvl))
            try:
                return await fn(*args, **kwargs)
            finally:
                for name, orig in original_log_methods.items():
                    setattr(context.log, name, orig)

        return async_wrapper
    else:
        return wrapper
