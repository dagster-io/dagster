import json
import logging
import sys
import threading
import traceback
from collections.abc import Mapping, Sequence
from contextlib import ExitStack
from typing import IO, TYPE_CHECKING, Any, Optional

from dagster_shared import seven

from dagster._core.log_manager import LOG_RECORD_METADATA_ATTR
from dagster._core.storage.compute_log_manager import ComputeIOType, ComputeLogManager
from dagster._core.utils import coerce_valid_log_level
from dagster._utils.error import serializable_error_info_from_exc_info
from dagster._utils.log import create_console_logger

if TYPE_CHECKING:
    from dagster._core.instance import DagsterInstance


class DispatchingLogHandler(logging.Handler):
    """Proxies logging records to a set of downstream loggers which themselves will route to their own
    set of handlers.  Needed to bridge to the set of dagster logging utilities which were
    implemented as loggers rather than log handlers.
    """

    def __init__(self, downstream_loggers: list[logging.Logger]):
        # Setting up a local thread context here to allow the DispatchingLogHandler
        # to be used in multi threading environments where the handler is called by
        # different threads with different log messages in parallel.
        self._local_thread_context = threading.local()
        self._local_thread_context.should_capture = True
        self._downstream_loggers = [*downstream_loggers]
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(self._local_thread_context, "should_capture"):
            # Since only the "main" thread gets an initialized
            # "_local_thread_context.should_capture" variable through the __init__()
            # we need to set a default value for all other threads here.
            self._local_thread_context.should_capture = True
        return self._local_thread_context.should_capture

    def emit(self, record: logging.LogRecord):
        """For any received record, add metadata, and have handlers handle it."""
        try:
            self._local_thread_context.should_capture = False
            for logger in self._downstream_loggers:
                logger.handle(record)
        finally:
            self._local_thread_context.should_capture = True


class CapturedLogHandler(logging.Handler):
    """Persist logging records to an IO stream controlled by the ComputeLogManager."""

    def __init__(self, write_stream: IO):
        self._write_stream = write_stream
        self._has_logged = False
        super().__init__()

    @property
    def has_logged(self):
        return self._has_logged

    def emit(self, record: logging.LogRecord):
        self._has_logged = True

        record_dict = record.__dict__
        exc_info = record_dict.get("exc_info")
        if exc_info:
            record_dict["exc_info"] = "".join(traceback.format_exception(*exc_info))

        try:
            self._write_stream.write(seven.json.dumps(record_dict) + "\n")
        except Exception:
            sys.stderr.write(
                f"Exception writing to logger event stream: {serializable_error_info_from_exc_info(sys.exc_info())}\n"
            )


class InstigationLogger(logging.Logger):
    """Logger exposed on the evaluation context of sensor/schedule evaluation functions.  This is tied
    to the Python logging system by setting up a custom logging handler that writes JSON payloads
    representing the log events to the dagster-managed captured log manager.  These log events are
    persisted, using the given log_key, which is stored on the sensor/schedule tick. These logs can
    then be retrieved using the log_key through captured log manager's API.

    The instigation logger also adds a console logger to emit the logs in a structured way from the
    evaluation process.
    """

    def __init__(
        self,
        log_key: Optional[Sequence[str]] = None,
        instance: Optional["DagsterInstance"] = None,
        repository_name: Optional[str] = None,
        instigator_name: Optional[str] = None,
        level: int = logging.NOTSET,
        logger_name: str = "dagster",
        console_logger: Optional[logging.Logger] = None,
    ):
        super().__init__(name=logger_name, level=coerce_valid_log_level(level))
        self._log_key = log_key
        self._instance = instance
        self._repository_name = repository_name
        self._instigator_name = instigator_name
        self._exit_stack = ExitStack()
        self._capture_handler = None
        if console_logger is None:
            console_logger = create_console_logger("dagster", logging.INFO)
        self.addHandler(DispatchingLogHandler([console_logger]))

    def __enter__(self):
        if (
            self._log_key
            and self._instance
            and isinstance(self._instance.compute_log_manager, ComputeLogManager)
        ):
            try:
                write_stream = self._exit_stack.enter_context(
                    self._instance.compute_log_manager.open_log_stream(
                        self._log_key, ComputeIOType.STDERR
                    )
                )
            except Exception:
                sys.stderr.write(
                    f"Exception initializing logger write stream: {serializable_error_info_from_exc_info(sys.exc_info())}\n"
                )
                write_stream = None

            if write_stream:
                self._capture_handler = CapturedLogHandler(write_stream)
                self.addHandler(self._capture_handler)
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        try:
            self._exit_stack.close()
        except Exception:
            sys.stderr.write(
                f"Exception closing logger write stream: {serializable_error_info_from_exc_info(sys.exc_info())}\n"
            )

    def _annotate_record(self, record: logging.LogRecord) -> logging.LogRecord:
        if self._repository_name and self._instigator_name:
            message = record.getMessage()
            setattr(
                record,
                LOG_RECORD_METADATA_ATTR,
                {
                    "repository_name": self._repository_name,
                    "name": self._instigator_name,
                    "orig_message": message,
                },
            )
            record.msg = " - ".join([self._repository_name, self._instigator_name, message])
            record.args = tuple()
        return record

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo):  # pyright: ignore[reportIncompatibleMethodOverride]
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        return self._annotate_record(record)

    def has_captured_logs(self):
        return self._capture_handler and self._capture_handler.has_logged


def get_instigation_log_records(
    instance: "DagsterInstance", log_key: Sequence[str]
) -> Sequence[Mapping[str, Any]]:
    log_data = instance.compute_log_manager.get_log_data(log_key)
    raw_logs = log_data.stderr.decode("utf-8") if log_data.stderr else ""

    records = []
    for line in raw_logs.split("\n"):
        if not line:
            continue

        try:
            records.append(seven.json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
