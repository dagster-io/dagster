import logging
from contextlib import ExitStack
from typing import IO, List, Optional

from dagster import _seven
from dagster._core.instance import DagsterInstance
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.utils import coerce_valid_log_level
from dagster._utils.log import create_console_logger


class InstigationLogHandler(logging.Handler):
    """
    The main purpose of this log handler is to proxy logging records to a set of downstream loggers
    which themselves will route to their own set of handlers
    """

    def __init__(self, downstream_loggers: List[logging.Logger]):
        self._should_capture = True
        self._downstream_loggers = [*downstream_loggers]
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        return self._should_capture

    def emit(self, record: logging.LogRecord):
        """For any received record, add metadata, and have handlers handle it"""

        try:
            self._should_capture = False
            for logger in self._downstream_loggers:
                logger.handle(record)
        finally:
            self._should_capture = True


class CapturedLogHandler(logging.Handler):
    """
    The main purpose of this log handler is to persist logging records to an IO stream controlled
    by the CapturedLogManager
    """

    def __init__(self, write_stream: IO):
        self._should_capture = True
        self._write_stream = write_stream
        self._has_logged = False
        super().__init__()

    @property
    def has_logged(self):
        return self._has_logged

    def emit(self, record: logging.LogRecord):
        self._has_logged = True
        self._write_stream.write(_seven.json.dumps(record.__dict__) + "\n")


class InstigationLogger(logging.Logger):
    def __init__(
        self,
        log_key: Optional[List[str]] = None,
        instance: Optional[DagsterInstance] = None,
        level: int = logging.NOTSET,
    ):
        super().__init__(name="dagster", level=coerce_valid_log_level(level))
        self._log_key = log_key
        self._instance = instance
        self._exit_stack = ExitStack()
        self._capture_handler = None
        self.addHandler(InstigationLogHandler([create_console_logger("dagster", logging.INFO)]))

    def __enter__(self):
        if (
            self._log_key
            and self._instance
            and isinstance(self._instance.compute_log_manager, CapturedLogManager)
        ):
            write_stream = self._exit_stack.enter_context(
                self._instance.compute_log_manager.open_log_stream(self._log_key)
            )
            if write_stream:
                self._capture_handler = CapturedLogHandler(write_stream)
                self.addHandler(self._capture_handler)
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    def has_captured_logs(self):
        return self._capture_handler and self._capture_handler.has_logged
