import json
import logging
from contextlib import ExitStack
from typing import IO, Any, List, Mapping, Optional, Sequence

from dagster import _seven
from dagster._core.instance import DagsterInstance
from dagster._core.log_manager import DAGSTER_META_KEY
from dagster._core.storage.captured_log_manager import CapturedLogManager
from dagster._core.storage.compute_log_manager import ComputeIOType
from dagster._core.utils import coerce_valid_log_level
from dagster._utils.log import create_console_logger


class DispatchingLogHandler(logging.Handler):
    """
    Proxies logging records to a set of downstream loggers which themselves will route to their own
    set of handlers.  Needed to bridge to the set of dagster logging utilities which were
    implemented as loggers rather than log handlers.
    """

    def __init__(self, downstream_loggers: List[logging.Logger]):
        self._should_capture = True
        self._downstream_loggers = [*downstream_loggers]
        super().__init__()

    def filter(self, record: logging.LogRecord) -> bool:
        return self._should_capture

    def emit(self, record: logging.LogRecord):
        """For any received record, add metadata, and have handlers handle it."""
        try:
            self._should_capture = False
            for logger in self._downstream_loggers:
                logger.handle(record)
        finally:
            self._should_capture = True


class CapturedLogHandler(logging.Handler):
    """
    Persist logging records to an IO stream controlled by the CapturedLogManager.
    """

    def __init__(self, write_stream: IO):
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
    """
    Logger exposed on the evaluation context of sensor/schedule evaluation functions.  This is tied
    to the Python logging system by setting up a custom logging handler that writes JSON payloads
    representing the log events to the dagster-managed captured log manager.  These log events are
    persisted, using the given log_key, which is stored on the sensor/schedule tick. These logs can
    then be retrieved using the log_key through captured log manager's API.

    The instigation logger also adds a console logger to emit the logs in a structured way from the
    evaluation process.
    """

    def __init__(
        self,
        log_key: Optional[List[str]] = None,
        instance: Optional[DagsterInstance] = None,
        repository_name: Optional[str] = None,
        name: Optional[str] = None,
        level: int = logging.NOTSET,
    ):
        super().__init__(name="dagster", level=coerce_valid_log_level(level))
        self._log_key = log_key
        self._instance = instance
        self._repository_name = repository_name
        self._name = name
        self._exit_stack = ExitStack()
        self._capture_handler = None
        self.addHandler(DispatchingLogHandler([create_console_logger("dagster", logging.INFO)]))

    def __enter__(self):
        if (
            self._log_key
            and self._instance
            and isinstance(self._instance.compute_log_manager, CapturedLogManager)
        ):
            write_stream = self._exit_stack.enter_context(
                self._instance.compute_log_manager.open_log_stream(
                    self._log_key, ComputeIOType.STDERR
                )
            )
            if write_stream:
                self._capture_handler = CapturedLogHandler(write_stream)
                self.addHandler(self._capture_handler)
        return self

    def __exit__(self, _exception_type, _exception_value, _traceback):
        self._exit_stack.close()

    def _annotate_record(self, record) -> logging.LogRecord:
        if self._repository_name and self._name:
            message = record.getMessage()
            setattr(
                record,
                DAGSTER_META_KEY,
                {
                    "repository_name": self._repository_name,
                    "name": self._name,
                    "orig_message": message,
                },
            )
            record.msg = " - ".join([self._repository_name, self._name, message])
        return record

    def makeRecord(  # pylint: disable=signature-differs
        self, name, level, fn, lno, msg, args, exc_info, func, extra, sinfo
    ):
        record = super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
        return self._annotate_record(record)

    def has_captured_logs(self):
        return self._capture_handler and self._capture_handler.has_logged


def get_instigation_log_records(
    instance: DagsterInstance, log_key: Sequence[str]
) -> Sequence[Mapping[str, Any]]:
    if not isinstance(instance.compute_log_manager, CapturedLogManager):
        return []

    log_data = instance.compute_log_manager.get_log_data(log_key)
    raw_logs = log_data.stderr.decode("utf-8") if log_data.stderr else ""

    records = []
    for line in raw_logs.split("\n"):
        if not line:
            continue

        try:
            records.append(_seven.json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
