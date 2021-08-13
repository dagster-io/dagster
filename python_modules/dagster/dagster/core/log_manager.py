import datetime
import itertools
import logging
from collections import OrderedDict, namedtuple
from typing import Any, Dict, NamedTuple, Optional

from dagster import check, seven
from dagster.core.utils import make_new_run_id
from dagster.utils import frozendict, merge_dicts
from dagster.utils.error import SerializableErrorInfo

DAGSTER_META_KEY = "dagster_meta"


PYTHON_LOGGING_LEVELS_MAPPING = frozendict(
    OrderedDict({"CRITICAL": 50, "ERROR": 40, "WARNING": 30, "INFO": 20, "DEBUG": 10})
)

PYTHON_LOGGING_LEVELS_ALIASES = frozendict(OrderedDict({"FATAL": "CRITICAL", "WARN": "WARNING"}))

PYTHON_LOGGING_LEVELS_NAMES = frozenset(
    [
        level_name.lower()
        for level_name in sorted(
            list(PYTHON_LOGGING_LEVELS_MAPPING.keys()) + list(PYTHON_LOGGING_LEVELS_ALIASES.keys())
        )
    ]
)


def _dump_value(value):
    # dump namedtuples as objects instead of arrays
    if isinstance(value, tuple) and hasattr(value, "_asdict"):
        return seven.json.dumps(value._asdict())

    return seven.json.dumps(value)


class DagsterMessageProps(
    NamedTuple(
        "_DagsterMessageProps",
        [
            ("orig_message", Optional[str]),
            ("log_message_id", Optional[str]),
            ("log_timestamp", Optional[str]),
            ("dagster_event", Optional["DagsterEvent"]),
        ],
    )
):
    """Internal class used to represent specific attributes about a logged message"""

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
                log_timestamp, "log_timestamp", default=datetime.datetime.utcnow().isoformat()
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

        if hasattr(event_specific_data, "error") and isinstance(
            event_specific_data.error, SerializableErrorInfo
        ):
            if hasattr(event_specific_data, "error_display_string"):
                return "\n\n" + event_specific_data.error_display_string
            return "\n\n" + event_specific_data.error.to_string()
        return None

    @property
    def pid(self) -> Optional[str]:
        if self.dagster_event is None or self.dagster_event.pid is None:
            return None
        return str(self.dagster_event.pid)

    @property
    def event_type_value(self) -> Optional[str]:
        if self.dagster_event is None:
            return None
        return self.dagster_event.event_type_value


class DagsterLoggingTags(
    NamedTuple(
        "_DagsterLoggingTags",
        [
            ("run_id", Optional[str]),
            ("pipeline_name", Optional[str]),
            ("pipeline_tags", Dict[str, str]),
            ("step_key", Optional[str]),
            ("solid_name", Optional[str]),
            ("resource_name", Optional[str]),
            ("resource_fn_name", Optional[str]),
        ],
    )
):
    """Internal class used to represent the context in which a given message was logged (i.e. the
    step, pipeline run, resource, etc.)
    """

    def __new__(
        cls,
        run_id: str = None,
        pipeline_name: str = None,
        pipeline_tags: Dict[str, str] = None,
        step_key: str = None,
        solid_name: str = None,
        resource_name: str = None,
        resource_fn_name: str = None,
    ):
        return super().__new__(
            cls,
            run_id=run_id,
            pipeline_name=pipeline_name,
            pipeline_tags=pipeline_tags or {},
            step_key=step_key,
            solid_name=solid_name,
            resource_name=resource_name,
            resource_fn_name=resource_fn_name,
        )

    @property
    def log_source(self):
        if self.resource_name is None:
            return self.pipeline_name or "system"
        return f"resource:{self.resource_name}"


def construct_log_string(
    logging_tags: DagsterLoggingTags, message_props: DagsterMessageProps
) -> str:

    return (
        " - ".join(
            filter(
                None,
                (
                    logging_tags.log_source,
                    logging_tags.run_id,
                    message_props.pid,
                    logging_tags.step_key,
                    message_props.event_type_value,
                    message_props.orig_message,
                ),
            )
        )
        + (message_props.error_str or "")
    )


def coerce_valid_log_level(log_level):
    """Convert a log level into an integer for consumption by the low-level Python logging API."""
    if isinstance(log_level, int):
        return log_level
    check.str_param(log_level, "log_level")
    check.invariant(
        log_level.lower() in PYTHON_LOGGING_LEVELS_NAMES,
        "Bad value for log level {level}: permissible values are {levels}.".format(
            level=log_level,
            levels=", ".join(
                ["'{}'".format(level_name.upper()) for level_name in PYTHON_LOGGING_LEVELS_NAMES]
            ),
        ),
    )
    log_level = PYTHON_LOGGING_LEVELS_ALIASES.get(log_level.upper(), log_level.upper())
    return PYTHON_LOGGING_LEVELS_MAPPING[log_level]


class DagsterLogManager(namedtuple("_DagsterLogManager", "logging_tags loggers")):
    """Centralized dispatch for logging from user code.

    Handles the construction of uniform structured log messages and passes them through to the
    underlying loggers.

    An instance of the log manager is made available to solids as ``context.log``. Users should not
    initialize instances of the log manager directly. To configure custom loggers, set the
    ``logger_defs`` on a :py:class:`ModeDefinition` for a pipeline.

    The log manager supports standard convenience methods like those exposed by the Python standard
    library :py:mod:`python:logging` module (i.e., within the body of a solid,
    ``context.log.{debug, info, warning, warn, error, critical, fatal}``).

    The underlying integer API can also be called directly using, e.g.
    ``context.log.log(5, msg)``, and the log manager will delegate to the ``log`` method
    defined on each of the loggers it manages.

    User-defined custom log levels are not supported, and calls to, e.g.,
    ``context.log.trace`` or ``context.log.notice`` will result in hard exceptions **at runtime**.
    """

    def __new__(cls, logging_tags, loggers):
        return super(DagsterLogManager, cls).__new__(
            cls,
            logging_tags=check.inst_param(logging_tags, "logging_tags", DagsterLoggingTags),
            loggers=check.list_param(loggers, "loggers", of_type=logging.Logger),
        )

    def with_tags(self, **new_tags):
        """Add new tags in "new_tags" to the set of tags attached to this log manager instance, and
        return a new DagsterLogManager with the merged set of tags.

        Args:
            tags (Dict[str,str]): Dictionary of tags

        Returns:
            DagsterLogManager: a new DagsterLogManager namedtuple with updated tags for the same
                run ID and loggers.
        """
        return self._replace(logging_tags=self.logging_tags._replace(**new_tags))

    def _prepare_message(self, orig_message, message_props):
        check.str_param(orig_message, "orig_message")
        check.dict_param(message_props, "message_props")

        # These are todos to further align with the Python logging API
        check.invariant(
            "extra" not in message_props, "do not allow until explicit support is handled"
        )
        check.invariant(
            "exc_info" not in message_props, "do not allow until explicit support is handled"
        )

        # Reserved keys in the message_props -- these are system generated.
        check.invariant("orig_message" not in message_props, "orig_message reserved value")
        check.invariant("message" not in message_props, "message reserved value")
        check.invariant("log_message_id" not in message_props, "log_message_id reserved value")
        check.invariant("log_timestamp" not in message_props, "log_timestamp reserved value")

        # structured information about this specific message
        dagster_message_props = DagsterMessageProps(
            orig_message=orig_message, dagster_event=message_props.get("dagster_event")
        )

        # We first generate all props for the purpose of producing the semi-structured
        # log message via _kv_messsage
        all_props = dict(
            itertools.chain(
                self.logging_tags._asdict().items(),
                message_props.items(),
                dagster_message_props._asdict().items(),
            )
        )

        # So here we use the arbitrary key DAGSTER_META_KEY to store a dictionary of
        # all the meta information that dagster injects into log message.
        # The python logging module, in its infinite wisdom, actually takes all the
        # keys in extra and unconditionally smashes them into the internal dictionary
        # of the logging.LogRecord class. We used a reserved key here to avoid naming
        # collisions with internal variables of the LogRecord class.
        # See __init__.py:363 (makeLogRecord) in the python 3.6 logging module source
        # for the gory details.
        return (
            construct_log_string(self.logging_tags, dagster_message_props),
            {DAGSTER_META_KEY: all_props},
        )

    def _log(self, level, orig_message, message_props):
        """Invoke the underlying loggers for a given log level.

        Args:
            level (Union[str, int]): An integer represeting a Python logging level or one of the
                standard Python string representations of a logging level.
            orig_message (str): The log message generated in user code.
            message_props (dict): Additional properties for the structured log message.
        """
        if not self.loggers:
            return

        level = coerce_valid_log_level(level)

        message, extra = self._prepare_message(orig_message, message_props)

        for logger_ in self.loggers:
            logger_.log(level, message, extra=extra)

    def log(self, level, msg, **kwargs):
        """Invoke the underlying loggers for a given integer log level.

        Args:
            level (int): An integer represeting a Python logging level.
            orig_message (str): The message to log.
        """

        check.str_param(msg, "msg")
        check.int_param(level, "level")
        return self._log(level, msg, kwargs)

    def debug(self, msg, **kwargs):
        """Log at the ``logging.DEBUG`` level.

        The message will be automatically adorned with contextual information about the name
        of the pipeline, the name of the solid, etc., so it is generally unnecessary to include
        this type of information in the log message.

        You can optionally additional key-value pairs to an individual log message using the kwargs
        to this method.

        Args:
            msg (str): The message to log.
            **kwargs (Optional[Any]): Any additional key-value pairs for only this log message.
        """

        check.str_param(msg, "msg")
        return self._log(logging.DEBUG, msg, kwargs)

    def info(self, msg, **kwargs):
        """Log at the ``logging.INFO`` level.

        See :py:meth:`~DagsterLogManager.debug`.
        """

        check.str_param(msg, "msg")
        return self._log(logging.INFO, msg, kwargs)

    def warning(self, msg, **kwargs):
        """Log at the ``logging.WARNING`` level.

        See :py:meth:`~DagsterLogManager.debug`.
        """

        check.str_param(msg, "msg")
        return self._log(logging.WARNING, msg, kwargs)

    # Define the alias .warn()
    warn = warning
    """Alias for :py:meth:`~DagsterLogManager.warning`"""

    def error(self, msg, **kwargs):
        """Log at the ``logging.ERROR`` level.

        See :py:meth:`~DagsterLogManager.debug`.
        """

        check.str_param(msg, "msg")
        return self._log(logging.ERROR, msg, kwargs)

    def critical(self, msg, **kwargs):
        """Log at the ``logging.CRITICAL`` level.

        See :py:meth:`~DagsterLogManager.debug`.
        """
        check.str_param(msg, "msg")
        return self._log(logging.CRITICAL, msg, kwargs)

    # Define the alias .fatal()
    fatal = critical
    """Alias for :py:meth:`~DagsterLogManager.critical`"""
