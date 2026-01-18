import datetime
import logging
import threading
from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Final, Optional, TypedDict, Union, cast

import dagster._check as check
from dagster._annotations import public
from dagster._core.utils import coerce_valid_log_level, make_new_run_id
from dagster._utils.log import get_dagster_logger

if TYPE_CHECKING:
    from dagster import DagsterInstance
    from dagster._core.events import DagsterEvent, DagsterEventBatchMetadata
    from dagster._core.storage.dagster_run import DagsterRun

# Python's logging system allows you to attach arbitrary values to a log message/record by passing a
# dictionary as `extra` to a logging method. The keys of extra are "splatted" directly into the
# `logging.LogRecord` created by this call-- i.e. `foo` will be set as an attribute on the
# `LogRecord`, not `extra`. The lack of an intervening abstraction between attached data and the
# `LogRecord` necessitates providing our own. There are only types of data that we attach: (1) a
# `DagsterEvent`; (2) a dictionary of assorted metadata about the context of the log message. The
# below APIs should be used for get/set/has operations on these types of data.

LOG_RECORD_EVENT_ATTR: Final = "dagster_event"


def get_log_record_event(record: logging.LogRecord) -> "DagsterEvent":
    return cast("DagsterEvent", getattr(record, LOG_RECORD_EVENT_ATTR))


def set_log_record_event(record: logging.LogRecord, event: "DagsterEvent") -> None:
    setattr(record, LOG_RECORD_EVENT_ATTR, event)


def has_log_record_event(record: logging.LogRecord) -> bool:
    return hasattr(record, LOG_RECORD_EVENT_ATTR)


LOG_RECORD_EVENT_BATCH_METADATA_ATTR: Final = "dagster_event_batch_metadata"


def get_log_record_event_batch_metadata(record: logging.LogRecord) -> "DagsterEventBatchMetadata":
    return cast("DagsterEventBatchMetadata", getattr(record, LOG_RECORD_EVENT_BATCH_METADATA_ATTR))


def set_log_record_event_batch_metadata(
    record: logging.LogRecord, event: "DagsterEventBatchMetadata"
) -> None:
    setattr(record, LOG_RECORD_EVENT_BATCH_METADATA_ATTR, event)


def has_log_record_event_batch_metadata(record: logging.LogRecord) -> bool:
    return hasattr(record, LOG_RECORD_EVENT_BATCH_METADATA_ATTR)


LOG_RECORD_METADATA_ATTR: Final = "dagster_meta"


def get_log_record_metadata(record: logging.LogRecord) -> "DagsterLogRecordMetadata":
    return getattr(record, LOG_RECORD_METADATA_ATTR)


def set_log_record_metadata(
    record: logging.LogRecord, metadata: "DagsterLogRecordMetadata"
) -> None:
    setattr(record, LOG_RECORD_METADATA_ATTR, metadata)


def has_log_record_metadata(record: logging.LogRecord) -> bool:
    return hasattr(record, LOG_RECORD_METADATA_ATTR)


class DagsterLogHandlerMetadata(TypedDict):
    """Internal class used to represent the context in which a given message was logged (i.e. the
    step, run, resource, etc.). This is stored on the `DagsterLogHandler` (and `DagsterLogManager`) and
    merged into the specific metadata for each log event to form a `DagsterLogRecordMetadata`
    instance.
    """

    run_id: Optional[str]
    job_name: Optional[str]
    job_tags: Mapping[str, str]
    step_key: Optional[str]
    op_name: Optional[str]
    resource_name: Optional[str]
    resource_fn_name: Optional[str]


class DagsterLogRecordMetadata(TypedDict):
    """Internal class representing the full metadata on a log record after it has been modified by
    the `DagsterLogHandler`. It contains all the fields on `DagsterLogHandlerMetadata`, an optional
    `DagsterEvent`, and some fields concerning the individual log message.
    """

    run_id: Optional[str]
    job_name: Optional[str]
    job_tags: Mapping[str, str]
    step_key: Optional[str]
    op_name: Optional[str]
    resource_name: Optional[str]
    resource_fn_name: Optional[str]
    dagster_event: Optional["DagsterEvent"]
    dagster_event_batch_metadata: Optional["DagsterEventBatchMetadata"]
    orig_message: str
    log_message_id: str
    log_timestamp: str


def construct_log_record_message(metadata: DagsterLogRecordMetadata) -> str:
    from dagster._core.events import EVENT_TYPE_TO_DISPLAY_STRING

    if metadata["resource_name"] is not None:
        log_source = f"resource:{metadata['resource_name']}"
    else:
        log_source = metadata["job_name"] or "system"

    if metadata["dagster_event"] is not None:
        event = metadata["dagster_event"]
        event_type_str = EVENT_TYPE_TO_DISPLAY_STRING.get(event.event_type, event.event_type.value)
        pid_str = str(event.pid) if event.pid else None
        error_str = _error_str_for_event(event)
    else:
        event_type_str = None
        pid_str = None
        error_str = None

    message_parts = filter(
        None,
        [
            log_source,
            metadata["run_id"],
            pid_str,
            metadata["step_key"],
            event_type_str,
            metadata["orig_message"],
        ],
    )
    return " - ".join(message_parts) + (error_str or "")


def _error_str_for_event(event: "DagsterEvent") -> Optional[str]:
    data = event.event_specific_data
    if data:
        error = getattr(data, "error", None)
        if error:
            error_display_string = getattr(data, "error_display_string", error.to_string())
            return f"\n\n{error_display_string}"
    return None


def construct_log_record_metadata(
    handler_metadata: DagsterLogHandlerMetadata,
    orig_message: str,
    event: Optional["DagsterEvent"],
    event_batch_metadata: Optional["DagsterEventBatchMetadata"],
) -> DagsterLogRecordMetadata:
    step_key = handler_metadata["step_key"] or (event.step_key if event else None)
    timestamp = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat()
    return DagsterLogRecordMetadata(
        run_id=handler_metadata["run_id"],
        job_name=handler_metadata["job_name"],
        job_tags=handler_metadata["job_tags"],
        op_name=handler_metadata["op_name"],
        resource_name=handler_metadata["resource_name"],
        resource_fn_name=handler_metadata["resource_fn_name"],
        orig_message=orig_message,
        log_message_id=make_new_run_id(),
        log_timestamp=timestamp,
        dagster_event=event,
        dagster_event_batch_metadata=event_batch_metadata,
        step_key=step_key,
    )


class DagsterLogHandler(logging.Handler):
    """Internal class used to turn regular logs into Dagster logs by adding Dagster-specific
    metadata (such as job_name or step_key), as well as reformatting the underlying message.

    Note: The `loggers` argument will be populated with the set of @loggers supplied to the current
    run. These essentially work as handlers (they do not create their own log messages, they simply
    re-log messages that are created from context.log.x() calls), which is why they are referenced
    from within this handler class.
    """

    def __init__(
        self,
        metadata: DagsterLogHandlerMetadata,
        loggers: Sequence[logging.Logger],
        handlers: Sequence[logging.Handler],
    ):
        self._metadata = metadata
        self._loggers = loggers
        self._handlers = handlers
        # Setting up a local thread context here to allow the DagsterLogHandler
        # to be used in multi threading environments where the handler is called by
        # different threads with different log messages in parallel.
        self._local_thread_context = threading.local()
        self._local_thread_context.should_capture = True
        super().__init__()

    @property
    def metadata(self) -> DagsterLogHandlerMetadata:
        return self._metadata

    def with_tags(self, **new_tags: str) -> "DagsterLogHandler":
        return DagsterLogHandler(
            metadata={**self._metadata, **cast("DagsterLogHandlerMetadata", new_tags)},
            loggers=self._loggers,
            handlers=self._handlers,
        )

    def _extract_extra(self, record: logging.LogRecord) -> Mapping[str, Any]:
        """In the logging.Logger log() implementation, the elements of the `extra` dictionary
        argument are smashed into the __dict__ of the underlying logging.LogRecord.
        This function figures out what the original `extra` values of the log call were by
        comparing the set of attributes in the received record to those of a default record.
        """
        ref_attrs = list(logging.makeLogRecord({}).__dict__.keys()) + [
            "message",
            "asctime",
        ]
        return {k: v for k, v in record.__dict__.items() if k not in ref_attrs}

    def _convert_record(self, record: logging.LogRecord) -> logging.LogRecord:
        # If this was a logged DagsterEvent, the event will be stored on the record
        event = get_log_record_event(record) if has_log_record_event(record) else None
        event_batch_metadata = (
            get_log_record_event_batch_metadata(record)
            if has_log_record_event_batch_metadata(record)
            else None
        )
        metadata = construct_log_record_metadata(
            self._metadata, record.getMessage(), event, event_batch_metadata
        )
        message = construct_log_record_message(metadata)

        # update the message to be formatted like other dagster logs
        set_log_record_metadata(record, metadata)
        record.msg = message
        record.args = ()
        return record

    def filter(self, record: logging.LogRecord) -> bool:
        """If you list multiple levels of a python logging hierarchy as managed loggers, and do not
        set the propagate attribute to False, this will result in that record getting logged
        multiple times, as the DagsterLogHandler will be invoked at each level of the hierarchy as
        the message is propagated. This filter prevents this from happening.
        """
        if not hasattr(self._local_thread_context, "should_capture"):
            # Since only the "main" thread gets an initialized
            # "_local_thread_context.should_capture" variable through the __init__()
            # we need to set a default value for all other threads here.
            self._local_thread_context.should_capture = True

        return self._local_thread_context.should_capture and not has_log_record_metadata(record)

    def emit(self, record: logging.LogRecord) -> None:
        """For any received record, add Dagster metadata, and have handlers handle it."""
        try:
            # to prevent the potential for infinite loops in which a handler produces log messages
            # which are then captured and then handled by that same handler (etc.), do not capture
            # any log messages while one is currently being emitted
            self._local_thread_context.should_capture = False
            dagster_record = self._convert_record(record)
            # built-in handlers
            for handler in self._handlers:
                if dagster_record.levelno >= handler.level:
                    handler.handle(dagster_record)
            # user-defined @loggers
            for logger in self._loggers:
                logger.log(
                    dagster_record.levelno,
                    dagster_record.msg,
                    exc_info=dagster_record.exc_info,
                    extra=self._extract_extra(record),
                )
        finally:
            self._local_thread_context.should_capture = True


@public
class DagsterLogManager(logging.Logger):
    """Centralized dispatch for logging from user code.

    Handles the construction of uniform structured log messages and passes them through to the
    underlying loggers/handlers.

    An instance of the log manager is made available to ops as ``context.log``. Users should not
    initialize instances of the log manager directly. To configure custom loggers, set the
    ``logger_defs`` argument in an `@job` decorator or when calling the `to_job()` method on a
    :py:class:`GraphDefinition`.

    The log manager inherits standard convenience methods like those exposed by the Python standard
    library :py:mod:`python:logging` module (i.e., within the body of an op,
    ``context.log.{debug, info, warning, warn, error, critical, fatal}``).

    The underlying integer API can also be called directly using, e.g.
    ``context.log.log(5, msg)``, and the log manager will delegate to the ``log`` method
    defined on each of the loggers it manages.

    User-defined custom log levels are not supported, and calls to, e.g.,
    ``context.log.trace`` or ``context.log.notice`` will result in hard exceptions **at runtime**.
    """

    def __init__(
        self,
        dagster_handler: DagsterLogHandler,
        level: int = logging.NOTSET,
        managed_loggers: Optional[Sequence[logging.Logger]] = None,
    ):
        super().__init__(name="dagster", level=coerce_valid_log_level(level))
        self._managed_loggers = check.opt_sequence_param(
            managed_loggers, "managed_loggers", of_type=logging.Logger
        )
        self._dagster_handler = dagster_handler
        self.addHandler(dagster_handler)

    @classmethod
    def create(
        cls,
        loggers: Sequence[logging.Logger],
        handlers: Optional[Sequence[logging.Handler]] = None,
        instance: Optional["DagsterInstance"] = None,
        dagster_run: Optional["DagsterRun"] = None,
    ) -> "DagsterLogManager":
        """Create a DagsterLogManager with a set of subservient loggers."""
        handlers = check.opt_sequence_param(handlers, "handlers", of_type=logging.Handler)

        managed_loggers = [get_dagster_logger()]
        python_log_level = logging.NOTSET

        if instance:
            handlers = [*handlers, *instance.get_handlers()]
            managed_loggers += [
                logging.getLogger(lname) if lname != "root" else logging.getLogger()
                for lname in instance.managed_python_loggers
            ]
            if instance.python_log_level is not None:
                python_log_level = coerce_valid_log_level(instance.python_log_level)

                # set all loggers to the declared logging level
                for logger in managed_loggers:
                    logger.setLevel(python_log_level)

        handler_metadata = DagsterLogHandlerMetadata(
            run_id=dagster_run.run_id if dagster_run else None,
            job_name=dagster_run.job_name if dagster_run else None,
            job_tags=dagster_run.tags if dagster_run else {},
            # These will be set on handlers for individual steps
            step_key=None,
            op_name=None,
            resource_name=None,
            resource_fn_name=None,
        )

        return cls(
            dagster_handler=DagsterLogHandler(
                metadata=handler_metadata,
                loggers=loggers,
                handlers=handlers,
            ),
            level=python_log_level,
            managed_loggers=managed_loggers,
        )

    @property
    def metadata(self) -> DagsterLogHandlerMetadata:
        return self._dagster_handler.metadata

    def begin_python_log_capture(self) -> None:
        for logger in self._managed_loggers:
            logger.addHandler(self._dagster_handler)

    def end_python_log_capture(self) -> None:
        for logger in self._managed_loggers:
            logger.removeHandler(self._dagster_handler)

    def log_dagster_event(
        self,
        level: Union[str, int],
        msg: str,
        dagster_event: "DagsterEvent",
        batch_metadata: Optional["DagsterEventBatchMetadata"] = None,
    ) -> None:
        """Log a DagsterEvent at the given level. Attributes about the context it was logged in
        (such as the asset or job name) will be automatically attached to the created record.

        Args:
            level (str, int): either a string representing the desired log level ("INFO", "WARN"),
                or an integer level such as logging.INFO or logging.DEBUG.
            msg (str): message describing the event
            dagster_event (DagsterEvent): DagsterEvent that will be logged
            batch_metadata (BatchMetadata): Metadata about the batch that the event is a part of.
        """
        self.log(
            level=level,
            msg=msg,
            extra={
                LOG_RECORD_EVENT_ATTR: dagster_event,
                LOG_RECORD_EVENT_BATCH_METADATA_ATTR: batch_metadata,
            },
        )

    def log(
        self,
        level: Union[str, int],
        msg: object,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Log a message at the given level. Attributes about the context it was logged in (such as
        the asset or job name) will be automatically attached to the created record.

        Args:
            level (str, int): either a string representing the desired log level ("INFO", "WARN"),
                or an integer level such as logging.INFO or logging.DEBUG.
            msg (str): the message to be logged
            *args: the logged message will be msg % args
        """
        level = coerce_valid_log_level(level)
        # log DagsterEvents regardless of level
        if self.isEnabledFor(level) or (
            "extra" in kwargs and LOG_RECORD_EVENT_ATTR in kwargs["extra"]
        ):
            self._log(level, msg, args, **kwargs)

    def with_tags(self, **new_tags: str) -> "DagsterLogManager":
        """Add new tags in "new_tags" to the set of tags attached to this log manager instance, and
        return a new DagsterLogManager with the merged set of tags.

        Args:
            new_tags (Dict[str,str]): Dictionary of tags

        Returns:
            DagsterLogManager: a new DagsterLogManager namedtuple with updated tags for the same
                run ID and loggers.
        """
        return DagsterLogManager(
            dagster_handler=self._dagster_handler.with_tags(**new_tags),
            managed_loggers=self._managed_loggers,
            level=self.level,
        )
