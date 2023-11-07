import datetime
import logging
from typing import TYPE_CHECKING, Any, Mapping, NamedTuple, Optional, Sequence, Union, cast

from typing_extensions import Protocol

import dagster._check as check
from dagster._core.utils import coerce_valid_log_level, make_new_run_id
from dagster._utils.log import get_dagster_logger

if TYPE_CHECKING:
    from dagster import DagsterInstance
    from dagster._core.events import DagsterEvent
    from dagster._core.storage.dagster_run import DagsterRun

DAGSTER_META_KEY = "dagster_meta"


class IDagsterMeta(Protocol):
    @property
    def dagster_meta(self) -> "DagsterLoggingMetadata":
        ...


# The type-checker complains here that DagsterLogRecord does not implement the `dagster_meta`
# property of `IDagsterMeta`. We ignore this error because we don't need to implement this method--
# `DagsterLogRecord` is a stub class that is never instantiated. We only ever cast
# `logging.LogRecord` objects to `DagsterLogRecord`, because it gives us typed access to the
# `dagster_meta` property. `dagster_meta` itself is set on these `logging.LogRecord` objects via the
# `extra` argument to `logging.Logger.log` (see `DagsterLogManager.log_dagster_event`), but
# `logging.LogRecord` has no way of exposing to the type-checker the attributes that are dynamically
# defined via `extra`.
class DagsterLogRecord(logging.LogRecord, IDagsterMeta):  # type: ignore
    pass


class DagsterMessageProps(
    NamedTuple(
        "_DagsterMessageProps",
        [
            ("orig_message", Optional[str]),
            ("log_message_id", Optional[str]),
            ("log_timestamp", Optional[str]),
            ("dagster_event", Optional[Any]),
        ],
    )
):
    """Internal class used to represent specific attributes about a logged message."""

    def __new__(
        cls,
        orig_message: str,
        log_message_id: Optional[str] = None,
        log_timestamp: Optional[str] = None,
        dagster_event: Optional["DagsterEvent"] = None,
    ):
        return super().__new__(
            cls,
            orig_message=check.str_param(orig_message, "orig_message"),
            log_message_id=check.opt_str_param(
                log_message_id, "log_message_id", default=make_new_run_id()
            ),
            log_timestamp=check.opt_str_param(
                log_timestamp,
                "log_timestamp",
                default=datetime.datetime.utcnow().isoformat(),
            ),
            dagster_event=dagster_event,
        )

    @property
    def error_str(self) -> Optional[str]:
        if self.dagster_event is None:
            return None

        event_specific_data = self.dagster_event.event_specific_data
        if not event_specific_data:
            return None

        error = getattr(event_specific_data, "error", None)
        if error:
            return f'\n\n{getattr(event_specific_data, "error_display_string", error.to_string())}'
        return None

    @property
    def pid(self) -> Optional[str]:
        if self.dagster_event is None or self.dagster_event.pid is None:
            return None
        return str(self.dagster_event.pid)

    @property
    def step_key(self) -> Optional[str]:
        if self.dagster_event is None:
            return None
        return self.dagster_event.step_key

    @property
    def event_type_value(self) -> Optional[str]:
        if self.dagster_event is None:
            return None
        return self.dagster_event.event_type_value


class DagsterLoggingMetadata(
    NamedTuple(
        "_DagsterLoggingMetadata",
        [
            ("run_id", Optional[str]),
            ("job_name", Optional[str]),
            ("job_tags", Mapping[str, str]),
            ("step_key", Optional[str]),
            ("op_name", Optional[str]),
            ("resource_name", Optional[str]),
            ("resource_fn_name", Optional[str]),
        ],
    )
):
    """Internal class used to represent the context in which a given message was logged (i.e. the
    step, pipeline run, resource, etc.).
    """

    def __new__(
        cls,
        run_id: Optional[str] = None,
        job_name: Optional[str] = None,
        job_tags: Optional[Mapping[str, str]] = None,
        step_key: Optional[str] = None,
        op_name: Optional[str] = None,
        resource_name: Optional[str] = None,
        resource_fn_name: Optional[str] = None,
    ):
        return super().__new__(
            cls,
            run_id=run_id,
            job_name=job_name,
            job_tags=job_tags or {},
            step_key=step_key,
            op_name=op_name,
            resource_name=resource_name,
            resource_fn_name=resource_fn_name,
        )

    @property
    def log_source(self) -> str:
        if self.resource_name is None:
            return self.job_name or "system"
        return f"resource:{self.resource_name}"

    def all_tags(self) -> Mapping[str, str]:
        # converts all values into strings
        return {k: str(v) for k, v in self._asdict().items()}

    def event_tags(self) -> Mapping[str, str]:
        # Exclude pipeline_tags since it can be quite large and can be found on the run
        return {k: str(v) for k, v in self._asdict().items() if k != "job_tags"}


def construct_log_string(
    logging_metadata: DagsterLoggingMetadata, message_props: DagsterMessageProps
) -> str:
    from dagster._core.events import EVENT_TYPE_VALUE_TO_DISPLAY_STRING

    event_type_str = (
        EVENT_TYPE_VALUE_TO_DISPLAY_STRING[message_props.event_type_value]
        if message_props.event_type_value in EVENT_TYPE_VALUE_TO_DISPLAY_STRING
        else message_props.event_type_value
    )
    return " - ".join(
        filter(
            None,
            (
                logging_metadata.log_source,
                logging_metadata.run_id,
                message_props.pid,
                logging_metadata.step_key,
                event_type_str,
                message_props.orig_message,
            ),
        )
    ) + (message_props.error_str or "")


def get_dagster_meta_dict(
    logging_metadata: DagsterLoggingMetadata, dagster_message_props: DagsterMessageProps
) -> Mapping[str, object]:
    # combine all dagster meta information into a single dictionary
    meta_dict = {
        **logging_metadata._asdict(),
        **dagster_message_props._asdict(),
    }
    # step-level events can be logged from a pipeline context. for these cases, pull the step
    # key from the underlying DagsterEvent
    if meta_dict["step_key"] is None:
        meta_dict["step_key"] = dagster_message_props.step_key

    return meta_dict


class DagsterLogHandler(logging.Handler):
    """Internal class used to turn regular logs into Dagster logs by adding Dagster-specific
    metadata (such as pipeline_name or step_key), as well as reformatting the underlying message.

    Note: The `loggers` argument will be populated with the set of @loggers supplied to the current
    pipeline run. These essentially work as handlers (they do not create their own log messages,
    they simply re-log messages that are created from context.log.x() calls), which is why they are
    referenced from within this handler class.
    """

    def __init__(
        self,
        logging_metadata: DagsterLoggingMetadata,
        loggers: Sequence[logging.Logger],
        handlers: Sequence[logging.Handler],
    ):
        self._logging_metadata = logging_metadata
        self._loggers = loggers
        self._handlers = handlers
        self._should_capture = True
        super().__init__()

    @property
    def logging_metadata(self) -> DagsterLoggingMetadata:
        return self._logging_metadata

    def with_tags(self, **new_tags: str) -> "DagsterLogHandler":
        return DagsterLogHandler(
            logging_metadata=self.logging_metadata._replace(**new_tags),
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

    def _convert_record(self, record: logging.LogRecord) -> DagsterLogRecord:
        # we store the originating DagsterEvent in the DAGSTER_META_KEY field, if applicable
        dagster_meta = getattr(record, DAGSTER_META_KEY, None)

        # generate some properties for this specific record
        dagster_message_props = DagsterMessageProps(
            orig_message=record.getMessage(), dagster_event=dagster_meta
        )

        # set the dagster meta info for the record
        setattr(
            record,
            DAGSTER_META_KEY,
            get_dagster_meta_dict(self._logging_metadata, dagster_message_props),
        )

        # update the message to be formatted like other dagster logs
        record.msg = construct_log_string(self._logging_metadata, dagster_message_props)
        record.args = ()

        # DagsterLogRecord is a LogRecord with a `dagster_meta` field
        return cast(DagsterLogRecord, record)

    def filter(self, record: logging.LogRecord) -> bool:
        """If you list multiple levels of a python logging hierarchy as managed loggers, and do not
        set the propagate attribute to False, this will result in that record getting logged
        multiple times, as the DagsterLogHandler will be invoked at each level of the hierarchy as
        the message is propagated. This filter prevents this from happening.
        """
        return self._should_capture and not isinstance(
            getattr(record, DAGSTER_META_KEY, None), dict
        )

    def emit(self, record: logging.LogRecord) -> None:
        """For any received record, add Dagster metadata, and have handlers handle it."""
        try:
            # to prevent the potential for infinite loops in which a handler produces log messages
            # which are then captured and then handled by that same handler (etc.), do not capture
            # any log messages while one is currently being emitted
            self._should_capture = False
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
            self._should_capture = True


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

        if dagster_run:
            logging_metadata = DagsterLoggingMetadata(
                run_id=dagster_run.run_id,
                job_name=dagster_run.job_name,
                job_tags=dagster_run.tags,
            )
        else:
            logging_metadata = DagsterLoggingMetadata()

        return cls(
            dagster_handler=DagsterLogHandler(
                logging_metadata=logging_metadata,
                loggers=loggers,
                handlers=handlers,
            ),
            level=python_log_level,
            managed_loggers=managed_loggers,
        )

    @property
    def logging_metadata(self) -> DagsterLoggingMetadata:
        return self._dagster_handler.logging_metadata

    def begin_python_log_capture(self) -> None:
        for logger in self._managed_loggers:
            logger.addHandler(self._dagster_handler)

    def end_python_log_capture(self) -> None:
        for logger in self._managed_loggers:
            logger.removeHandler(self._dagster_handler)

    def log_dagster_event(
        self, level: Union[str, int], msg: str, dagster_event: "DagsterEvent"
    ) -> None:
        """Log a DagsterEvent at the given level. Attributes about the context it was logged in
        (such as the solid name or pipeline name) will be automatically attached to the created record.

        Args:
            level (str, int): either a string representing the desired log level ("INFO", "WARN"),
                or an integer level such as logging.INFO or logging.DEBUG.
            msg (str): message describing the event
            dagster_event (DagsterEvent): DagsterEvent that will be logged
        """
        self.log(level=level, msg=msg, extra={DAGSTER_META_KEY: dagster_event})

    def log(self, level: Union[str, int], msg: object, *args: Any, **kwargs: Any) -> None:
        """Log a message at the given level. Attributes about the context it was logged in (such as
        the solid name or pipeline name) will be automatically attached to the created record.

        Args:
            level (str, int): either a string representing the desired log level ("INFO", "WARN"),
                or an integer level such as logging.INFO or logging.DEBUG.
            msg (str): the message to be logged
            *args: the logged message will be msg % args
        """
        level = coerce_valid_log_level(level)
        # log DagsterEvents regardless of level
        if self.isEnabledFor(level) or ("extra" in kwargs and DAGSTER_META_KEY in kwargs["extra"]):
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
